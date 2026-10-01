from fastapi import HTTPException
from sqlalchemy import and_, exists, func, or_, select

from APP.models.album import Album, album_artists
from APP.models.artist import Artist
from APP.models.event import Event
from APP.models.event_log import EventLog
from APP.models.follow import Follow
from APP.models.playlist import Playlist
from APP.models.rating import Rating
from APP.models.review import Review
from APP.models.track import Track
from APP.models.track_artist import TrackArtist
from APP.models.user import User
from APP.models.venue import Venue
from APP.schemas.event_log import ActivityOut
from APP.schemas.follow import FollowOut
from APP.schemas.pagination import Page
from APP.schemas.user import UserShort
from APP.services.activity import record_event
from APP.services.ratings import lock_user

FOLLOW_MODELS = {"user": User, "artist": Artist, "venue": Venue}


async def set_follow(session, user, kind, target_id, remove=False):
    async with session.begin():
        await lock_user(session, user.id)
        if kind == "user" and user.id == target_id:
            raise HTTPException(status_code=409, detail="Cannot follow yourself")
        model = FOLLOW_MODELS[kind]
        # KEY SHARE не конфликтует с блокировкой другого подписчика.
        target = await session.scalar(
            select(model)
            .where(model.id == target_id)
            .with_for_update(read=True, key_share=True, of=model)
        )
        if target is None or (kind == "user" and not target.is_active):
            raise HTTPException(status_code=404, detail="Follow target not found")
        follow = await session.scalar(
            select(Follow).where(
                Follow.follower_id == user.id,
                Follow.target_type == kind,
                Follow.target_id == target_id,
            )
        )
        changed = False
        if remove:
            if follow is not None:
                await session.delete(follow)
                changed = True
            output = None
        else:
            if follow is None:
                follow = Follow(
                    follower_id=user.id,
                    target_type=kind,
                    target_id=target_id,
                    **{f"{kind}_id": target_id},
                )
                session.add(follow)
                await session.flush()
                changed = True
            output = FollowOut.model_validate(follow)
        if changed:
            record_event(
                session,
                user.id,
                "follow_removed" if remove else "follow_added",
                kind,
                target_id,
            )
    return output


async def following_page(session, user, limit, offset):
    query = select(Follow).where(Follow.follower_id == user.id)
    rows = list(
        (
            await session.scalars(
                query.order_by(Follow.created_at.desc(), Follow.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    total = await session.scalar(
        select(func.count()).select_from(Follow).where(Follow.follower_id == user.id)
    )
    return Page(
        items=[FollowOut.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def visible_activity():
    models = {
        "user": User,
        "artist": Artist,
        "album": Album,
        "track": Track,
        "venue": Venue,
        "event": Event,
        "review": Review,
        "playlist": Playlist,
    }
    conditions = []
    for kind, model in models.items():
        filters = [model.id == EventLog.target_id]
        if kind == "playlist":
            filters.extend([Playlist.visibility == "public", Playlist.kind == "custom"])
        if kind == "user":
            filters.append(User.is_active.is_(True))
        conditions.append(
            and_(
                EventLog.target_type == kind,
                exists(select(model.id).where(*filters).correlate(EventLog)),
            )
        )
    return or_(*conditions)


def subscribed_activity(user_id):
    users = select(Follow.user_id).where(
        Follow.follower_id == user_id, Follow.target_type == "user"
    )
    artists = select(Follow.artist_id).where(
        Follow.follower_id == user_id, Follow.target_type == "artist"
    )
    venues = select(Follow.venue_id).where(
        Follow.follower_id == user_id, Follow.target_type == "venue"
    )
    tracks = select(TrackArtist.track_id).where(TrackArtist.artist_id.in_(artists))
    albums = select(album_artists.c.album_id).where(
        album_artists.c.artist_id.in_(artists)
    )
    reviews = (
        select(Review.id)
        .join(Rating)
        .where(
            or_(
                and_(Rating.target_type == "artist", Rating.target_id.in_(artists)),
                and_(Rating.target_type == "track", Rating.target_id.in_(tracks)),
                and_(Rating.target_type == "album", Rating.target_id.in_(albums)),
                and_(Rating.target_type == "venue", Rating.target_id.in_(venues)),
            )
        )
    )
    return or_(
        EventLog.actor_id.in_(users),
        and_(EventLog.target_type == "artist", EventLog.target_id.in_(artists)),
        and_(EventLog.target_type == "track", EventLog.target_id.in_(tracks)),
        and_(EventLog.target_type == "album", EventLog.target_id.in_(albums)),
        and_(EventLog.target_type == "venue", EventLog.target_id.in_(venues)),
        and_(
            EventLog.target_type == "event",
            EventLog.target_id.in_(select(Event.id).where(Event.venue_id.in_(venues))),
        ),
        and_(EventLog.target_type == "review", EventLog.target_id.in_(reviews)),
    )


async def feed_page(session, user, limit, offset):
    filters = [
        EventLog.is_public.is_(True),
        visible_activity(),
        subscribed_activity(user.id),
    ]
    rows = (
        await session.execute(
            select(EventLog, User)
            .outerjoin(User, EventLog.actor_id == User.id)
            .where(*filters)
            .order_by(EventLog.created_at.desc(), EventLog.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    total = await session.scalar(
        select(func.count()).select_from(EventLog).where(*filters)
    )
    items = [
        ActivityOut(
            id=row.EventLog.id,
            actor=UserShort.model_validate(row.User) if row.User is not None else None,
            action=row.EventLog.action,
            target_type=row.EventLog.target_type,
            target_id=row.EventLog.target_id,
            payload=row.EventLog.payload,
            created_at=row.EventLog.created_at,
        )
        for row in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)
