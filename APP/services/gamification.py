from datetime import UTC, date, datetime, timedelta
from hashlib import sha256

from fastapi import HTTPException
from sqlalchemy import distinct, func, select

from APP.core.constants import (
    DEFAULT_CONTRIBUTION_POINTS,
    DEFAULT_EVENT_ATTENDANCE_MILESTONE,
    DEFAULT_FIRST_ARTIST_POINTS,
    DEFAULT_MONTHLY_REVIEWERS,
    DEFAULT_PUBLICATION_DAILY_CAP,
    DEFAULT_PUBLICATION_POINTS,
    DEFAULT_REVIEW_LIKES_MILESTONE,
    DEFAULT_STREAK_DAYS,
    DEFAULT_TRACK_LISTENERS_MILESTONE,
    DEFAULT_VENUE_MONTHLY_EVENTS,
    DEFAULT_VENUE_MONTHLY_POINTS,
    REVIEW_XP_MIN_LENGTH,
)
from APP.models.artist import Artist
from APP.models.event import Event
from APP.models.event_attendance import EventAttendance
from APP.models.experience_award import ExperienceAward
from APP.models.favorite import Favorite
from APP.models.listening_session import ListeningSession
from APP.models.media import Media
from APP.models.rating import Rating
from APP.models.review import Review
from APP.models.review_reward_text import ReviewRewardText
from APP.models.track import Track
from APP.models.track_artist import TrackArtist
from APP.models.user import User
from APP.models.venue import Venue
from APP.schemas.experience import ExperienceAwardOut
from APP.schemas.pagination import Page
from APP.services.experience import award, experience_output, lock_active_user


async def capped_award(session, user, settings, kind, key, points, cap, track_id=None):
    now = datetime.now(UTC)
    count = await session.scalar(
        select(func.count())
        .select_from(ExperienceAward)
        .where(
            ExperienceAward.user_id == user.id,
            ExperienceAward.kind == kind,
            ExperienceAward.day == now.date(),
        )
    )
    if count >= cap:
        return False
    return await award(session, user, settings, track_id, key, kind, points, now)


async def micro_award(session, user, action, target_type, target_id):
    settings = session.info.get("settings")
    if settings is None:
        return
    await capped_award(
        session,
        user,
        settings,
        "micro",
        f"{action}:{target_type}:{target_id}",
        1,
        settings.micro_daily_cap,
        target_id if target_type == "track" else None,
    )


async def review_award(session, user, rating, text):
    settings = session.info.get("settings")
    if settings is None or len("".join(text.split())) <= REVIEW_XP_MIN_LENGTH:
        return
    from APP.services.ratings import TARGET_MODELS

    target = await session.get(TARGET_MODELS[rating.target_type], rating.target_id)
    if target is None or target.user_id == user.id:
        return
    # Один текст и одна цель дают награду однократно даже после удаления рецензии.
    fingerprint = sha256(" ".join(text.split()).casefold().encode()).hexdigest()
    seen = await session.scalar(
        select(ReviewRewardText.digest).where(
            ReviewRewardText.user_id == user.id, ReviewRewardText.digest == fingerprint
        )
    )
    if seen is not None:
        return
    rewarded = await capped_award(
        session,
        user,
        settings,
        "review",
        f"review:{rating.target_type}:{rating.target_id}",
        settings.review_points,
        settings.review_daily_cap,
        rating.track_id,
    )
    if rewarded:
        session.add(ReviewRewardText(user_id=user.id, digest=fingerprint))
        await session.flush()


async def contribution_award(session, proposal, settings):
    author = await lock_active_user(session, proposal.user_id)
    kind = proposal.target_type if proposal.field == "publication" else proposal.field
    return await award(
        session,
        author,
        settings,
        proposal.track_id,
        f"contribution:{proposal.target_type}:{proposal.target_id}:{proposal.field}",
        "contribution",
        DEFAULT_CONTRIBUTION_POINTS[kind],
        datetime.now(UTC),
    )


async def claim_milestones(session, actor, settings):
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
            )
        ).all()
        for track_id in tracks:
            # Публикация без внешнего отклика не даёт XP; важен результат для слушателей.
            audience = await session.scalar(
                select(func.count(distinct(ListeningSession.user_id)))
                .join(User, User.id == ListeningSession.user_id)
                .where(
                    ListeningSession.track_id == track_id,
                    ListeningSession.seconds >= ListeningSession.required_seconds,
                    ListeningSession.user_id != user.id,
                    User.is_active.is_(True),
                )
            )
            if audience >= 1:
                await capped_award(
                    session,
                    user,
                    settings,
                    "publication",
                    f"publication:{track_id}",
                    DEFAULT_PUBLICATION_POINTS,
                    DEFAULT_PUBLICATION_DAILY_CAP,
                    track_id,
                )
            if audience >= DEFAULT_TRACK_LISTENERS_MILESTONE:
                await award(
                    session,
                    user,
                    settings,
                    track_id,
                    f"track_audience:{track_id}",
                    "track_audience",
                    settings.milestone_points,
                    now,
                )
            quality_award = await session.scalar(
                select(ExperienceAward.id).where(
                    ExperienceAward.user_id == user.id,
                    ExperienceAward.source_key == f"quality:{track_id}",
                )
            )
            if quality_award is not None:
                artist_ids = (
                    await session.scalars(
                        select(Artist.id)
                        .join(TrackArtist, TrackArtist.artist_id == Artist.id)
                        .where(
                            TrackArtist.track_id == track_id, Artist.user_id == user.id
                        )
                    )
                ).all()
                for artist_id in artist_ids:
                    await award(
                        session,
                        user,
                        settings,
                        track_id,
                        f"artist_discovery:{artist_id}",
                        "artist_discovery",
                        DEFAULT_FIRST_ARTIST_POINTS,
                        now,
                    )
        reviews = (
            await session.execute(
                select(Review.id, Rating.target_type, Rating.target_id)
                .join(Rating)
                .where(
                    Rating.user_id == user.id,
                    func.length(func.trim(Review.text)) > REVIEW_XP_MIN_LENGTH,
                )
            )
        ).all()
        for review_id, target_type, target_id in reviews:
            likes = await session.scalar(
                select(func.count())
                .select_from(Favorite)
                .join(User)
                .where(
                    Favorite.review_id == review_id,
                    Favorite.user_id != user.id,
                    User.is_active.is_(True),
                )
            )
            if likes >= DEFAULT_REVIEW_LIKES_MILESTONE:
                await award(
                    session,
                    user,
                    settings,
                    None,
                    f"review_likes:{target_type}:{target_id}",
                    "review_likes",
                    settings.milestone_points,
                    now,
                )
        events = (
            await session.scalars(
                select(Event.id).where(
                    Event.user_id == user.id, Event.publication_status == "published"
                )
            )
        ).all()
        for event_id in events:
            attendance = await session.scalar(
                select(func.count())
                .select_from(EventAttendance)
                .join(User)
                .where(
                    EventAttendance.event_id == event_id,
                    EventAttendance.user_id != user.id,
                    User.is_active.is_(True),
                )
            )
            if attendance >= DEFAULT_EVENT_ATTENDANCE_MILESTONE:
                await award(
                    session,
                    user,
                    settings,
                    None,
                    f"event_audience:{event_id}",
                    "event_audience",
                    settings.milestone_points,
                    now,
                )
        meaningful_days = set(
            (
                await session.scalars(
                    select(distinct(ExperienceAward.day)).where(
                        ExperienceAward.user_id == user.id,
                        ExperienceAward.kind.in_(["listen", "review", "contribution"]),
                        ExperienceAward.day
                        >= now.date() - timedelta(days=DEFAULT_STREAK_DAYS - 1),
                    )
                )
            ).all()
        )
        if all(
            now.date() - timedelta(days=delta) in meaningful_days
            for delta in range(DEFAULT_STREAK_DAYS)
        ):
            # Удваивается только дневной XP за прослушивания; награды за качество не умножаются.
            today_listens = (
                await session.scalars(
                    select(ExperienceAward).where(
                        ExperienceAward.user_id == user.id,
                        ExperienceAward.kind == "listen",
                        ExperienceAward.day == now.date(),
                    )
                )
            ).all()
            for listening in today_listens:
                await award(
                    session,
                    user,
                    settings,
                    listening.track_id,
                    f"streak:{listening.source_key}",
                    "streak",
                    listening.points,
                    now,
                )
        for venue in (
            await session.scalars(
                select(Venue).where(
                    Venue.user_id == user.id, Venue.publication_status == "published"
                )
            )
        ).all():
            # Месячный бонус - за состоявшиеся события с реальными участниками.
            month = func.date_trunc("month", Event.stop_at)
            completed = (
                await session.execute(
                    select(month, func.count())
                    .select_from(Event)
                    .where(
                        Event.venue_id == venue.id,
                        Event.publication_status == "published",
                        Event.stop_at <= now,
                        select(EventAttendance.event_id)
                        .join(User)
                        .where(
                            EventAttendance.event_id == Event.id,
                            EventAttendance.user_id != user.id,
                            User.is_active.is_(True),
                        )
                        .exists(),
                    )
                    .group_by(month)
                    .having(func.count() >= DEFAULT_VENUE_MONTHLY_EVENTS)
                )
            ).all()
            for month_start, count in completed:
                await award(
                    session,
                    user,
                    settings,
                    None,
                    f"venue_month:{venue.id}:{month_start:%Y-%m}",
                    "venue_month",
                    DEFAULT_VENUE_MONTHLY_POINTS,
                    now,
                )
        output = experience_output(user, settings)
    return output


async def award_history(session, user, limit, offset):
    filters = [ExperienceAward.user_id == user.id]
    rows = (
        await session.scalars(
            select(ExperienceAward)
            .where(*filters)
            .order_by(ExperienceAward.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return Page[ExperienceAwardOut](
        items=[ExperienceAwardOut.model_validate(row) for row in rows],
        total=await session.scalar(
            select(func.count()).select_from(ExperienceAward).where(*filters)
        ),
        limit=limit,
        offset=offset,
    )


async def community_award(session, actor, target_id, payload, settings):
    period = date.fromisoformat(payload.period)
    if payload.kind == "curator_week" and period.weekday() != 0:
        raise HTTPException(
            status_code=422, detail="Weekly award period must be a Monday"
        )
    if payload.kind == "reviewer_month" and period.day != 1:
        raise HTTPException(
            status_code=422, detail="Monthly award period must be the first day"
        )
    if period > datetime.now(UTC).date():
        raise HTTPException(status_code=422, detail="Cannot award future periods")
    async with session.begin():
        from APP.services.admin import locked_users

        user = await locked_users(session, actor, target_id)
        if not user.is_active:
            raise HTTPException(status_code=409, detail="User is inactive")
        key = f"{payload.kind}:{period}"
        await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(key))))
        already = await session.scalar(
            select(ExperienceAward.id).where(
                ExperienceAward.user_id == target_id, ExperienceAward.source_key == key
            )
        )
        winners = await session.scalar(
            select(func.count())
            .select_from(ExperienceAward)
            .where(ExperienceAward.source_key == key)
        )
        if already is None and winners >= (
            1 if payload.kind == "curator_week" else DEFAULT_MONTHLY_REVIEWERS
        ):
            raise HTTPException(
                status_code=409,
                detail="All winners for this period have already been selected",
            )
        await award(
            session,
            user,
            settings,
            None,
            key,
            payload.kind,
            settings.milestone_points,
            datetime.now(UTC),
        )
        from APP.services.activity import record_event

        record_event(
            session,
            actor.id,
            "community_award_selected",
            "user",
            target_id,
            public=False,
            payload=payload.model_dump(),
        )
        output = experience_output(user, settings)
    return output
