from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select, update

from APP.core.constants import (
    EXPERIENCE_LEVEL_NAMES,
    LISTEN_COMPLETION_RATIO,
    LISTEN_HEARTBEAT_MAX_SECONDS,
    LISTEN_SESSION_TTL_HOURS,
    UserLevel,
)
from APP.models.artist import Artist
from APP.models.experience_award import ExperienceAward
from APP.models.listening_session import ListeningSession
from APP.models.media import Media
from APP.models.rating import Rating
from APP.models.track import Track
from APP.models.track_artist import TrackArtist
from APP.models.user import User
from APP.schemas.experience import ExperienceOut, ListeningOut
from APP.services.activity import record_event


def thresholds(settings):
    return [
        settings.experience_lyrics_points,
        settings.experience_genres_points,
        settings.experience_scene_points,
        *settings.experience_higher_thresholds,
    ]


def experience_tier(user, settings):
    return sum(
        user.experience_points >= threshold for threshold in thresholds(settings)
    )


def experience_output(user, settings):
    tier = experience_tier(user, settings)
    return ExperienceOut(
        experience_points=user.experience_points,
        experience_tier=tier,
        experience_level=tier + 1,
        level_name=EXPERIENCE_LEVEL_NAMES[tier],
        thresholds=[0, *thresholds(settings)],
        contribution_limit=settings.contribution_limits[tier],
        event_limit=settings.event_legend_limit
        if tier == len(thresholds(settings))
        else settings.event_active_limit,
        votes_required=settings.contribution_votes_required,
        micro_daily_cap=settings.micro_daily_cap,
        review_daily_cap=settings.review_daily_cap,
        review_points=settings.review_points,
        milestone_points=settings.milestone_points,
        next_threshold=thresholds(settings)[tier]
        if tier < len(thresholds(settings))
        else None,
        lyrics_threshold=settings.experience_lyrics_points,
        genres_threshold=settings.experience_genres_points,
        scene_threshold=settings.experience_scene_points,
        listen_daily_cap=settings.listen_daily_cap,
        quality_track_points=settings.quality_track_points,
        quality_min_raters=settings.quality_min_raters,
        quality_min_rating=float(settings.quality_min_rating),
    )


def sync_experience_level(user, settings):
    if user.level in (UserLevel.green, UserLevel.experienced):
        user.level = (
            UserLevel.experienced
            if experience_tier(user, settings)
            else UserLevel.green
        )


async def award(session, user, settings, track_id, source_key, kind, points, now):
    if (
        await session.scalar(
            select(ExperienceAward.id).where(
                ExperienceAward.user_id == user.id,
                ExperienceAward.source_key == source_key,
            )
        )
        is not None
    ):
        return False
    session.add(
        ExperienceAward(
            user_id=user.id,
            track_id=track_id,
            source_key=source_key,
            kind=kind,
            day=now.date(),
            points=points,
        )
    )
    user.experience_points += points
    sync_experience_level(user, settings)
    record_event(
        session,
        user.id,
        "experience_awarded",
        "user",
        user.id,
        public=False,
        payload={"kind": kind, "points": points, "track_id": track_id},
    )
    await session.flush()
    return True


async def lock_active_user(session, user_id):
    from APP.services.ratings import lock_user

    user = await lock_user(session, user_id)
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    return user


async def start_listening(session, actor, track_id, settings):
    now = datetime.now(UTC)
    async with session.begin():
        user = await lock_active_user(session, actor.id)
        row = (
            await session.execute(
                select(Track, Media)
                .join(Media, Track.audio_media_id == Media.id)
                .where(
                    Track.id == track_id, Media.status == "ready", Media.kind == "audio"
                )
            )
        ).one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Playable track not found")
        own_artist = await session.scalar(
            select(TrackArtist.track_id)
            .join(Artist)
            .where(TrackArtist.track_id == track_id, Artist.user_id == user.id)
            .limit(1)
        )
        if row.Track.user_id == user.id or own_artist is not None:
            raise HTTPException(
                status_code=409, detail="Own tracks do not award listening experience"
            )
        await session.execute(
            update(ListeningSession)
            .where(
                ListeningSession.user_id == user.id, ListeningSession.ended_at.is_(None)
            )
            .values(ended_at=now)
        )
        listening = ListeningSession(
            user_id=user.id,
            track_id=track_id,
            last_seen_at=now,
            expires_at=now + timedelta(hours=LISTEN_SESSION_TTL_HOURS),
            required_seconds=row.Media.duration * Decimal(LISTEN_COMPLETION_RATIO),
        )
        session.add(listening)
        await session.flush()
        output = ListeningOut(
            id=listening.id,
            seconds=float(listening.seconds),
            required_seconds=float(listening.required_seconds),
            experience=experience_output(user, settings),
        )
    return output


async def heartbeat(session, actor, listening_id, is_playing, settings):
    now = datetime.now(UTC)
    async with session.begin():
        user = await lock_active_user(session, actor.id)
        listening = await session.scalar(
            select(ListeningSession)
            .where(
                ListeningSession.id == listening_id, ListeningSession.user_id == user.id
            )
            .with_for_update()
        )
        if listening is None or listening.expires_at <= now:
            raise HTTPException(
                status_code=404, detail="Listening session not found or expired"
            )
        awarded = False
        if listening.ended_at is None:
            elapsed = max(
                0,
                min(
                    (now - listening.last_seen_at).total_seconds(),
                    LISTEN_HEARTBEAT_MAX_SECONDS,
                ),
            )
            if listening.is_playing:
                listening.seconds += Decimal(str(elapsed))
            listening.last_seen_at, listening.is_playing = now, is_playing
            if listening.seconds >= listening.required_seconds:
                daily = await session.scalar(
                    select(func.count())
                    .select_from(ExperienceAward)
                    .where(
                        ExperienceAward.user_id == user.id,
                        ExperienceAward.kind == "listen",
                        ExperienceAward.day == now.date(),
                    )
                )
                if daily < settings.listen_daily_cap:
                    awarded = await award(
                        session,
                        user,
                        settings,
                        listening.track_id,
                        f"listen:{listening.track_id}:{now.date()}",
                        "listen",
                        1,
                        now,
                    )
                listening.ended_at = now
            await session.flush()
        output = ListeningOut(
            id=listening.id,
            seconds=float(listening.seconds),
            required_seconds=float(listening.required_seconds),
            awarded=awarded,
            experience=experience_output(user, settings),
        )
    return output


async def claim_quality(session, actor, settings, track_id=None):
    now = datetime.now(UTC)
    async with session.begin():
        user = await lock_active_user(session, actor.id)
        tracks = (
            await session.scalars(
                select(Track.id)
                .join(Media, Track.audio_media_id == Media.id)
                .where(
                    Track.user_id == user.id,
                    Media.status == "ready",
                    Media.kind == "audio",
                )
                .order_by(Track.id)
            )
        ).all()
        if track_id is not None:
            tracks = [value for value in tracks if value == track_id]
        for track_id in tracks:
            count, average = (
                await session.execute(
                    select(func.count(), func.avg(Rating.value))
                    .join(User, User.id == Rating.user_id)
                    .where(
                        Rating.track_id == track_id,
                        Rating.user_id != user.id,
                        User.is_active.is_(True),
                    )
                )
            ).one()
            if (
                count >= settings.quality_min_raters
                and average >= settings.quality_min_rating
            ):
                await award(
                    session,
                    user,
                    settings,
                    track_id,
                    f"quality:{track_id}",
                    "quality",
                    settings.quality_track_points,
                    now,
                )
        output = experience_output(user, settings)
    return output
