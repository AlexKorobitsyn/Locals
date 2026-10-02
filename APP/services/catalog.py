from typing import Literal

from fastapi import HTTPException, status
from pydantic import AnyHttpUrl
from sqlalchemy import delete, func, select, true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from APP.core.config import Settings
from APP.core.constants import DEFAULT_ARTIST_ROLE
from APP.core.dependencies import require_owner_or_privileged
from APP.models.album import Album, album_artists
from APP.models.artist import Artist
from APP.models.city import City
from APP.models.event_log import EventLog
from APP.models.genre import Genre
from APP.models.track import Track
from APP.models.track_artist import TrackArtist
from APP.models.user import User
from APP.schemas.album import AlbumCreate, AlbumOut, AlbumRatedShort
from APP.schemas.artist import ArtistCreate, ArtistOut, ArtistRatedShort
from APP.schemas.genre import GenreCreate, GenreOut
from APP.schemas.pagination import Page
from APP.schemas.track import (
    TrackArtistInput,
    TrackCreate,
    TrackOut,
    TrackRatedShort,
)
from APP.services.engagement import set_engagement, with_engagement
from APP.services.ratings import (
    rating_average_expression,
    set_rating_context,
    with_my_rating,
)

CatalogKind = Literal["artist", "album", "track"]
MODELS = {"artist": Artist, "album": Album, "track": Track}
DETAIL_SCHEMAS = {"artist": ArtistOut, "album": AlbumOut, "track": TrackOut}
LIST_SCHEMAS = {
    "artist": ArtistRatedShort,
    "album": AlbumRatedShort,
    "track": TrackRatedShort,
}
DETAIL_LOADERS = {
    "artist": [selectinload(Artist.city), selectinload(Artist.genres)],
    "album": [selectinload(Album.artists), selectinload(Album.genres)],
    "track": [
        selectinload(Track.album).selectinload(Album.artists),
        selectinload(Track.artists),
        selectinload(Track.artist_credits).selectinload(TrackArtist.artist),
        selectinload(Track.genres),
    ],
}


def not_found(entity: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity} not found"
    )


def record_catalog_event(
    session: AsyncSession, user: User, kind: str, entity_id: int, action: str
) -> None:
    session.add(
        EventLog(
            actor_id=user.id,
            action=action,
            target_type=kind,
            target_id=entity_id,
            payload={},
            is_public=True,
        )
    )


async def related_rows(
    session: AsyncSession, model, ids: list[int], owner: User | None = None
) -> list:
    unique_ids = sorted(set(ids))
    query = select(model).where(model.id.in_(unique_ids)).order_by(model.id)
    if owner is not None:
        query = query.with_for_update()
    rows = list((await session.scalars(query)).all()) if unique_ids else []
    if len(rows) != len(unique_ids):
        raise not_found(model.__name__)
    if owner is not None:
        for row in rows:
            require_owner_or_privileged(row.user_id, owner)
    return rows


async def check_city(session: AsyncSession, city_id: int | None) -> None:
    if city_id is not None and await session.get(City, city_id) is None:
        raise not_found("City")


async def check_album(session: AsyncSession, album_id: int | None, user: User) -> None:
    if album_id is None:
        return
    album = await session.scalar(
        select(Album).where(Album.id == album_id).with_for_update()
    )
    if album is None:
        raise not_found("Album")
    require_owner_or_privileged(album.user_id, user)


def scalar_values(payload, excluded: set[str]) -> dict:
    return {
        key: str(value) if isinstance(value, AnyHttpUrl) else value
        for key, value in payload.model_dump(
            exclude_unset=True, exclude=excluded
        ).items()
    }


def detail_query(kind: CatalogKind):
    model = MODELS[kind]
    query = select(model).options(*DETAIL_LOADERS[kind])
    if kind == "artist":
        query = query.add_columns(
            select(func.count())
            .select_from(album_artists)
            .where(album_artists.c.artist_id == Artist.id)
            .scalar_subquery()
            .label("albums_count"),
            select(func.count(func.distinct(TrackArtist.track_id)))
            .where(TrackArtist.artist_id == Artist.id)
            .scalar_subquery()
            .label("tracks_count"),
        )
    elif kind == "album":
        query = query.add_columns(
            select(func.count())
            .select_from(Track)
            .where(Track.album_id == Album.id)
            .scalar_subquery()
            .label("tracks_count"),
            select(func.coalesce(func.sum(Track.duration), 0))
            .where(Track.album_id == Album.id)
            .scalar_subquery()
            .label("duration"),
        )
    return query


async def get_detail(
    session: AsyncSession,
    kind: CatalogKind,
    entity_id: int,
    viewer: User | None,
    settings: Settings,
):
    model = MODELS[kind]
    row = (
        await session.execute(
            with_engagement(
                with_my_rating(detail_query(kind), model, kind, viewer),
                model,
                kind,
                viewer,
            )
            .where(model.id == entity_id)
            .execution_options(populate_existing=True)
        )
    ).one_or_none()
    if row is None:
        raise not_found(model.__name__)
    entity = row[0]
    output = DETAIL_SCHEMAS[kind].model_validate(entity)
    output.is_owner = viewer is not None and viewer.id == entity.user_id
    for key in ("albums_count", "tracks_count", "duration"):
        if key in row._mapping:
            setattr(output, key, row._mapping[key])
    return set_engagement(set_rating_context(output, row.my_rating, settings), row)


def sort_columns(kind: CatalogKind, sort: str, settings: Settings, model=None):
    model = model if model is not None else MODELS[kind]
    descending = sort.startswith("-")
    name = sort.removeprefix("-")
    name = {"createdAt": "created_at", "releaseDate": "release_date"}.get(name, name)
    fields = {
        "id": model.id,
        "created_at": model.created_at,
        "ratings_count": model.ratings_count,
        "rating_avg": rating_average_expression(model, settings),
    }
    fields["name" if kind == "artist" else "title"] = (
        model.name if kind == "artist" else model.title
    )
    if kind == "album":
        fields["release_date"] = model.release_date
    if kind == "track":
        fields["duration"] = model.duration
    if name not in fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid sort field; allowed: {', '.join(sorted(fields))}",
        )
    column = fields[name]
    ordered = (column.desc() if descending else column.asc()).nulls_last()
    return (
        [ordered]
        if name == "id"
        else [ordered, model.id.desc() if descending else model.id.asc()]
    )


async def list_catalog(
    session: AsyncSession,
    kind: CatalogKind,
    viewer: User | None,
    limit: int,
    offset: int,
    sort: str,
    settings: Settings,
    artist_id: int | None = None,
    album_id: int | None = None,
    *,
    owner_id: int | None = None,
):
    model = MODELS[kind]
    filters = []
    if owner_id is not None:
        filters.append(model.user_id == owner_id)
    if artist_id is not None and kind == "album":
        filters.append(Album.artists.any(Artist.id == artist_id))
    if artist_id is not None and kind == "track":
        filters.append(Track.artists.any(Artist.id == artist_id))
    if album_id is not None and kind == "track":
        filters.append(Track.album_id == album_id)
    ordering = sort_columns(kind, sort, settings)
    # Один snapshot для total и страницы при конкурентном пополнении каталога.
    total = (
        select(func.count().label("total"))
        .select_from(model)
        .where(*filters)
        .subquery()
    )
    page_query = (
        select(model)
        .where(*filters)
        .order_by(*ordering)
        .limit(limit)
        .offset(offset)
        .subquery()
    )
    entity = aliased(model, page_query)
    # LEFT JOIN сохраняет total, даже если offset вышел за конец списка.
    query = (
        select(entity, total.c.total)
        .select_from(total.outerjoin(page_query, true()))
        .order_by(*sort_columns(kind, sort, settings, entity))
    )
    if kind == "album":
        query = query.options(selectinload(entity.artists))
    rows = (
        await session.execute(
            with_engagement(
                with_my_rating(query, entity, kind, viewer), entity, kind, viewer
            )
        )
    ).all()
    return Page(
        items=[
            set_engagement(
                set_rating_context(
                    LIST_SCHEMAS[kind].model_validate(row[0]), row.my_rating, settings
                ),
                row,
            )
            for row in rows
            if row[0] is not None
        ],
        total=rows[0].total,
        limit=limit,
        offset=offset,
    )


async def create_artist(
    session: AsyncSession, payload: ArtistCreate, user: User, settings: Settings
):
    async with session.begin():
        await check_city(session, payload.city_id)
        genres = await related_rows(session, Genre, payload.genre_ids)
        artist = Artist(
            **scalar_values(payload, {"genre_ids"}), user_id=user.id, genres=genres
        )
        artist.owner_fields = (
            ["metadata", "genres"] if payload.genre_ids else ["metadata"]
        )
        session.add(artist)
        await session.flush()
        record_catalog_event(session, user, "artist", artist.id, "artist_created")
        output = await get_detail(session, "artist", artist.id, user, settings)
    return output


async def create_album(
    session: AsyncSession, payload: AlbumCreate, user: User, settings: Settings
):
    async with session.begin():
        artists = await related_rows(session, Artist, payload.artist_ids, user)
        genres = await related_rows(session, Genre, payload.genre_ids)
        album = Album(
            **scalar_values(payload, {"artist_ids", "genre_ids"}),
            user_id=user.id,
            artists=artists,
            genres=genres,
        )
        album.owner_fields = (
            ["metadata", "genres"] if payload.genre_ids else ["metadata"]
        )
        session.add(album)
        await session.flush()
        record_catalog_event(session, user, "album", album.id, "album_created")
        output = await get_detail(session, "album", album.id, user, settings)
    return output


def track_credits(payload) -> list[TrackArtistInput]:
    credits = payload.artist_credits or [
        TrackArtistInput(artist_id=artist_id, role=DEFAULT_ARTIST_ROLE)
        for artist_id in payload.artist_ids or []
    ]
    if not credits:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="At least one artist is required",
        )
    return credits


async def resolve_credits(
    session: AsyncSession, payload, user: User
) -> list[TrackArtist]:
    credits = track_credits(payload)
    await related_rows(session, Artist, [credit.artist_id for credit in credits], user)
    return [
        TrackArtist(artist_id=credit.artist_id, role=credit.role) for credit in credits
    ]


async def create_track(
    session: AsyncSession, payload: TrackCreate, user: User, settings: Settings
):
    async with session.begin():
        await check_album(session, payload.album_id, user)
        credits = await resolve_credits(session, payload, user)
        genres = await related_rows(session, Genre, payload.genre_ids)
        track = Track(
            **scalar_values(payload, {"artist_ids", "artist_credits", "genre_ids"}),
            user_id=user.id,
            artist_credits=credits,
            genres=genres,
        )
        track.owner_fields = (
            ["metadata", "genres"] if payload.genre_ids else ["metadata"]
        )
        if payload.lyrics:
            track.owner_fields.append("lyrics")
        session.add(track)
        await session.flush()
        record_catalog_event(session, user, "track", track.id, "track_created")
        output = await get_detail(session, "track", track.id, user, settings)
    return output


async def update_catalog(
    session: AsyncSession,
    kind: CatalogKind,
    entity_id: int,
    payload,
    user: User,
    settings: Settings,
):
    model = MODELS[kind]
    async with session.begin():
        entity = await session.scalar(
            select(model)
            .where(model.id == entity_id)
            .options(*DETAIL_LOADERS[kind])
            .with_for_update()
        )
        if entity is None:
            raise not_found(model.__name__)
        require_owner_or_privileged(entity.user_id, user)
        fields = payload.model_fields_set
        if entity.user_id == user.id:
            protected = set(entity.owner_fields)
            if "genre_ids" in fields:
                protected.add("genres")
            if "lyrics" in fields:
                protected.add("lyrics")
            if "title" in fields or "name" in fields:
                protected.add("metadata")
            entity.owner_fields = sorted(protected)
        if "city_id" in fields:
            await check_city(session, payload.city_id)
        if "album_id" in fields:
            await check_album(session, payload.album_id, user)
        if "genre_ids" in fields:
            entity.genres = await related_rows(session, Genre, payload.genre_ids)
        if kind == "album" and "artist_ids" in fields:
            entity.artists = await related_rows(
                session, Artist, payload.artist_ids, user
            )
        if kind == "track" and fields & {"artist_ids", "artist_credits"}:
            # Удаление старых credits до INSERT позволяет повторно использовать роли.
            entity.artist_credits.clear()
            await session.flush()
            entity.artist_credits = await resolve_credits(session, payload, user)
        for key, value in scalar_values(
            payload, {"genre_ids", "artist_ids", "artist_credits"}
        ).items():
            setattr(entity, key, value)
            if key in ("cover_url", "image_url"):
                entity.image_media_id = None
        await session.flush()
        record_catalog_event(session, user, kind, entity.id, f"{kind}_updated")
        output = await get_detail(session, kind, entity.id, user, settings)
    return output


async def list_genres(session: AsyncSession, limit: int, offset: int) -> Page[GenreOut]:
    rows = list(
        (
            await session.scalars(
                select(Genre).order_by(Genre.name, Genre.id).limit(limit).offset(offset)
            )
        ).all()
    )
    total = await session.scalar(select(func.count()).select_from(Genre))
    return Page(
        items=[GenreOut.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


async def create_genre(
    session: AsyncSession, payload: GenreCreate, user: User
) -> GenreOut:
    try:
        async with session.begin():
            genre = Genre(**payload.model_dump())
            session.add(genre)
            await session.flush()
            record_catalog_event(session, user, "genre", genre.id, "genre_created")
            output = GenreOut.model_validate(genre)
        return output
    except IntegrityError as exc:
        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Genre slug already exists"
            ) from None
        raise


async def delete_catalog(session, kind, entity_id, actor):
    model = MODELS[kind]
    async with session.begin():
        entity = await session.scalar(
            select(model).where(model.id == entity_id).with_for_update()
        )
        if entity is None:
            raise not_found(model.__name__)
        if kind == "artist":
            credits = await session.scalar(
                select(func.count())
                .select_from(TrackArtist)
                .where(TrackArtist.artist_id == entity_id)
            )
            albums = await session.scalar(
                select(func.count())
                .select_from(album_artists)
                .where(album_artists.c.artist_id == entity_id)
            )
            if credits or albums:
                raise HTTPException(
                    status_code=409,
                    detail="Remove the artist from tracks and albums first",
                )
        if kind == "track":
            from APP.models.playlist_track import PlaylistTrack

            used = await session.scalar(
                select(func.count())
                .select_from(PlaylistTrack)
                .where(PlaylistTrack.track_id == entity_id)
            )
            if used:
                raise HTTPException(
                    status_code=409,
                    detail="Remove this track from custom playlists first",
                )
        record_catalog_event(session, actor, kind, entity_id, kind + "_deleted")
        await session.execute(delete(model).where(model.id == entity_id))
