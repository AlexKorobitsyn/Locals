from fastapi import HTTPException
from pydantic import AnyHttpUrl
from sqlalchemy import case, exists, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from APP.core.constants import PLAYLIST_MAX_TRACKS, FavoriteTarget, PlaylistKind
from APP.core.dependencies import require_owner
from APP.models.album import Album
from APP.models.artist import Artist
from APP.models.event import Event
from APP.models.favorite import Favorite
from APP.models.playlist import Playlist
from APP.models.playlist_track import PlaylistTrack
from APP.models.rating import Rating
from APP.models.review import Review
from APP.models.track import Track
from APP.models.venue import Venue
from APP.schemas.favorite import FavoriteRead
from APP.schemas.pagination import Page
from APP.schemas.playlist import PlaylistOut, PlaylistShort, PlaylistTrackItem
from APP.schemas.track import TrackRatedShort
from APP.services.activity import record_event
from APP.services.engagement import set_engagement, with_engagement
from APP.services.ratings import (
    lock_target,
    lock_user,
    set_rating_context,
    with_my_rating,
)

FAVORITE_MODELS = {
    "track": Track,
    "album": Album,
    "artist": Artist,
    "playlist": Playlist,
    "event": Event,
    "venue": Venue,
    "review": Review,
}


def visible_playlist(viewer):
    return or_(
        Playlist.visibility == "public",
        Playlist.user_id == viewer.id if viewer is not None else literal(False),
    )


async def ensure_liked(session: AsyncSession, user_id: int) -> Playlist:
    playlist = await session.scalar(
        select(Playlist).where(
            Playlist.user_id == user_id, Playlist.kind == PlaylistKind.liked
        )
    )
    if playlist is None:
        playlist = Playlist(
            user_id=user_id, name="Liked", kind=PlaylistKind.liked, visibility="private"
        )
        session.add(playlist)
        await session.flush()
        record_event(
            session, user_id, "playlist_created", "playlist", playlist.id, public=False
        )
    return playlist


def playlist_query(viewer):
    count = case(
        (
            Playlist.kind == PlaylistKind.liked,
            select(func.count())
            .select_from(Favorite)
            .where(
                Favorite.user_id == Playlist.user_id,
                Favorite.entity_type == FavoriteTarget.track,
            )
            .correlate(Playlist)
            .scalar_subquery(),
        ),
        else_=select(func.count())
        .select_from(PlaylistTrack)
        .where(PlaylistTrack.playlist_id == Playlist.id)
        .correlate(Playlist)
        .scalar_subquery(),
    ).label("tracks_count")
    return with_engagement(
        select(Playlist).options(selectinload(Playlist.owner)).add_columns(count),
        Playlist,
        "playlist",
        viewer,
    )


def playlist_output(row, viewer, details=True):
    output = (PlaylistOut if details else PlaylistShort).model_validate(row.Playlist)
    output.tracks_count = row.tracks_count
    output.is_owner = viewer is not None and viewer.id == row.Playlist.user_id
    return set_engagement(output, row)


async def get_playlist(session, playlist_id, viewer, lock=False):
    query = select(Playlist).where(Playlist.id == playlist_id, visible_playlist(viewer))
    if lock:
        query = query.with_for_update()
    playlist = await session.scalar(query)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist


async def playlist_detail(session, playlist_id, viewer):
    row = (
        await session.execute(
            playlist_query(viewer)
            .where(Playlist.id == playlist_id, visible_playlist(viewer))
            .execution_options(populate_existing=True)
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist_output(row, viewer)


async def list_playlists(session, viewer, limit, offset, scope="public"):
    if scope in ("own", "saved"):
        async with session.begin():
            await lock_user(session, viewer.id)
            await ensure_liked(session, viewer.id)
            return await _playlist_page(session, viewer, limit, offset, scope)
    return await _playlist_page(session, viewer, limit, offset, scope)


async def _playlist_page(session, viewer, limit, offset, scope):
    filters = [visible_playlist(viewer)]
    if scope == "own":
        filters.append(Playlist.user_id == viewer.id)
    elif scope == "saved":
        filters.extend(
            [
                Playlist.user_id != viewer.id,
                exists().where(
                    Favorite.user_id == viewer.id, Favorite.playlist_id == Playlist.id
                ),
            ]
        )
    else:
        filters.extend(
            [Playlist.visibility == "public", Playlist.kind == PlaylistKind.custom]
        )
    rows = (
        await session.execute(
            playlist_query(viewer)
            .where(*filters)
            .order_by(Playlist.created_at.desc(), Playlist.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    total = await session.scalar(
        select(func.count()).select_from(Playlist).where(*filters)
    )
    return Page(
        items=[playlist_output(row, viewer, details=False) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def playlist_values(payload):
    return {
        key: str(value) if isinstance(value, AnyHttpUrl) else value
        for key, value in payload.model_dump(exclude_unset=True).items()
    }


async def create_playlist(session, payload, user):
    async with session.begin():
        await lock_user(session, user.id)
        playlist = Playlist(
            user_id=user.id, kind=PlaylistKind.custom, **playlist_values(payload)
        )
        session.add(playlist)
        await session.flush()
        record_event(
            session,
            user.id,
            "playlist_created",
            "playlist",
            playlist.id,
            public=playlist.visibility == "public",
        )
        output = await playlist_detail(session, playlist.id, user)
    return output


def editable_playlist(playlist, user):
    require_owner(playlist.user_id, user)
    if playlist.kind == PlaylistKind.liked:
        raise HTTPException(
            status_code=409, detail="Liked is managed through track favorites"
        )


async def change_playlist(session, playlist_id, user, payload=None):
    async with session.begin():
        await lock_user(session, user.id)
        playlist = await get_playlist(session, playlist_id, user, lock=True)
        editable_playlist(playlist, user)
        if payload is None:
            record_event(
                session,
                user.id,
                "playlist_deleted",
                "playlist",
                playlist.id,
                public=playlist.visibility == "public",
            )
            await session.delete(playlist)
            output = None
        else:
            for key, value in playlist_values(payload).items():
                setattr(playlist, key, value)
                if key == "cover_url":
                    playlist.image_media_id = None
            await session.flush()
            record_event(
                session,
                user.id,
                "playlist_updated",
                "playlist",
                playlist.id,
                public=playlist.visibility == "public",
            )
            output = await playlist_detail(session, playlist.id, user)
    return output


async def playlist_tracks(session, playlist_id, viewer, settings, limit, offset):
    playlist = await get_playlist(session, playlist_id, viewer)
    if playlist.kind == PlaylistKind.liked:
        source = (
            select(
                Track,
                (
                    func.row_number().over(
                        order_by=(Favorite.created_at.desc(), Favorite.id.desc())
                    )
                    - 1
                ).label("position"),
                Favorite.created_at.label("added_at"),
            )
            .join(Favorite, Favorite.track_id == Track.id)
            .where(
                Favorite.user_id == playlist.user_id,
                Favorite.entity_type == FavoriteTarget.track,
            )
            .order_by(Favorite.created_at.desc(), Favorite.id.desc())
        )
        count = (
            select(func.count())
            .select_from(Favorite)
            .where(
                Favorite.user_id == playlist.user_id,
                Favorite.entity_type == FavoriteTarget.track,
            )
        )
    else:
        source = (
            select(Track, PlaylistTrack.position, PlaylistTrack.added_at)
            .join(PlaylistTrack, PlaylistTrack.track_id == Track.id)
            .where(PlaylistTrack.playlist_id == playlist_id)
            .order_by(PlaylistTrack.position, Track.id)
        )
        count = (
            select(func.count())
            .select_from(PlaylistTrack)
            .where(PlaylistTrack.playlist_id == playlist_id)
        )
    query = with_engagement(
        with_my_rating(source, Track, "track", viewer), Track, "track", viewer
    )
    rows = (await session.execute(query.limit(limit).offset(offset))).all()
    items = [
        PlaylistTrackItem(
            track=set_engagement(
                set_rating_context(
                    TrackRatedShort.model_validate(row.Track), row.my_rating, settings
                ),
                row,
            ),
            position=row.position,
            added_at=row.added_at,
        )
        for row in rows
    ]
    return Page(
        items=items, total=await session.scalar(count), limit=limit, offset=offset
    )


async def change_tracks(
    session, playlist_id, user, operation, payload=None, track_id=None
):
    async with session.begin():
        await lock_user(session, user.id)
        playlist = await get_playlist(session, playlist_id, user, lock=True)
        editable_playlist(playlist, user)
        items = list(
            (
                await session.scalars(
                    select(PlaylistTrack)
                    .where(PlaylistTrack.playlist_id == playlist_id)
                    .order_by(PlaylistTrack.position)
                )
            ).all()
        )
        if operation == "add":
            if len(items) >= PLAYLIST_MAX_TRACKS:
                raise HTTPException(
                    status_code=409, detail="Playlist track limit reached"
                )
            if any(item.track_id == payload.track_id for item in items):
                raise HTTPException(status_code=409, detail="Track already in playlist")
            if await session.get(Track, payload.track_id) is None:
                raise HTTPException(status_code=404, detail="Track not found")
            position = len(items) if payload.position is None else payload.position
            if position > len(items):
                raise HTTPException(
                    status_code=422, detail="Position exceeds playlist length"
                )
            item = PlaylistTrack(
                playlist_id=playlist_id, track_id=payload.track_id, position=position
            )
            items.insert(position, item)
            session.add(item)
        elif operation == "remove":
            found = next((item for item in items if item.track_id == track_id), None)
            if found is not None:
                items.remove(found)
                await session.delete(found)
        else:
            if set(payload.track_ids) != {item.track_id for item in items}:
                raise HTTPException(
                    status_code=409,
                    detail="Reorder must include every current track exactly once",
                )
            by_id = {item.track_id: item for item in items}
            items = [by_id[value] for value in payload.track_ids]
        for index, item in enumerate(items):
            item.position = index
        playlist.updated_at = func.now()
        await session.flush()
        record_event(
            session,
            user.id,
            f"playlist_tracks_{operation}",
            "playlist",
            playlist.id,
            public=playlist.visibility == "public",
        )


async def favorite_target(session, kind, entity_id, user, remove=False):
    model = FAVORITE_MODELS[kind]
    if kind == "review":
        rating = await session.scalar(
            select(Rating).join(Review).where(Review.id == entity_id)
        )
        if rating is None:
            raise HTTPException(status_code=404, detail="Review not found")
        await lock_target(session, rating.target_type, rating.target_id)
    target = await session.scalar(
        select(model).where(model.id == entity_id).with_for_update()
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Favorite target not found")
    if kind == "playlist" and not remove:
        if target.visibility == "private" and target.user_id != user.id:
            raise HTTPException(status_code=404, detail="Playlist not found")
        if target.kind == PlaylistKind.liked:
            raise HTTPException(
                status_code=409, detail="Cannot favorite the system playlist"
            )
    return target


async def set_favorite(session, kind, entity_id, user, remove=False):
    async with session.begin():
        await lock_user(session, user.id)
        favorite = await session.scalar(
            select(Favorite).where(
                Favorite.user_id == user.id,
                Favorite.entity_type == kind,
                Favorite.entity_id == entity_id,
            )
        )
        if remove and favorite is None:
            return None
        target = await favorite_target(session, kind, entity_id, user, remove=remove)
        changed = False
        if remove:
            if favorite is not None:
                await session.delete(favorite)
                changed = True
            output = None
        else:
            if kind == "track":
                await ensure_liked(session, user.id)
            if favorite is None:
                favorite = Favorite(
                    user_id=user.id,
                    entity_type=kind,
                    entity_id=entity_id,
                    **{f"{kind}_id": entity_id},
                )
                session.add(favorite)
                await session.flush()
                changed = True
            output = FavoriteRead.model_validate(favorite)
        if changed:
            record_event(
                session,
                user.id,
                "favorite_removed" if remove else "favorite_added",
                kind,
                entity_id,
                public=kind != "playlist" or target.visibility == "public",
            )
    return output


async def list_favorites(session, user, limit, offset, kind=None):
    filters = [
        Favorite.user_id == user.id,
        or_(
            Favorite.entity_type != "playlist",
            exists().where(Playlist.id == Favorite.playlist_id, visible_playlist(user)),
        ),
    ]
    if kind is not None:
        filters.append(Favorite.entity_type == kind)
    rows = list(
        (
            await session.scalars(
                select(Favorite)
                .where(*filters)
                .order_by(Favorite.created_at.desc(), Favorite.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    total = await session.scalar(
        select(func.count()).select_from(Favorite).where(*filters)
    )
    return Page(
        items=[FavoriteRead.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
