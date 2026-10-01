from fastapi import APIRouter, Response, status

from APP.core.config import SettingsDependency
from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency, OptionalUserDependency
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.schemas.playlist import (
    PlaylistCreate,
    PlaylistOut,
    PlaylistReorder,
    PlaylistShort,
    PlaylistTrackAdd,
    PlaylistTrackItem,
    PlaylistUpdate,
)
from APP.services.library import (
    change_playlist,
    change_tracks,
    create_playlist,
    list_playlists,
    playlist_detail,
    playlist_tracks,
)

router = APIRouter(tags=["playlists"])


@router.post(
    "/playlists", response_model=PlaylistOut, status_code=status.HTTP_201_CREATED
)
async def create(
    payload: PlaylistCreate, session: SessionDependency, user: CurrentUserDependency
):
    return await create_playlist(session, payload, user)


@router.get(
    "/playlists", response_model=Page[PlaylistShort], openapi_extra={"security": [{}]}
)
async def listing(
    session: SessionDependency,
    viewer: OptionalUserDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
):
    response.headers["Cache-Control"] = "no-store"
    return await list_playlists(session, viewer, limit, offset)


@router.get("/me/playlists", response_model=Page[PlaylistShort])
async def own(
    session: SessionDependency,
    user: CurrentUserDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
):
    response.headers["Cache-Control"] = "no-store"
    return await list_playlists(session, user, limit, offset, scope="own")


@router.get("/me/saved-playlists", response_model=Page[PlaylistShort])
async def saved(
    session: SessionDependency,
    user: CurrentUserDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
):
    response.headers["Cache-Control"] = "no-store"
    return await list_playlists(session, user, limit, offset, scope="saved")


@router.get(
    "/playlists/{playlist_id}",
    response_model=PlaylistOut,
    openapi_extra={"security": [{}]},
)
async def detail(
    playlist_id: EntityId,
    session: SessionDependency,
    viewer: OptionalUserDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await playlist_detail(session, playlist_id, viewer)


@router.patch("/playlists/{playlist_id}", response_model=PlaylistOut)
async def update(
    playlist_id: EntityId,
    payload: PlaylistUpdate,
    session: SessionDependency,
    user: CurrentUserDependency,
):
    return await change_playlist(session, playlist_id, user, payload)


@router.delete("/playlists/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    playlist_id: EntityId, session: SessionDependency, user: CurrentUserDependency
):
    await change_playlist(session, playlist_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/playlists/{playlist_id}/tracks",
    response_model=Page[PlaylistTrackItem],
    openapi_extra={"security": [{}]},
)
async def tracks(
    playlist_id: EntityId,
    session: SessionDependency,
    viewer: OptionalUserDependency,
    settings: SettingsDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
):
    response.headers["Cache-Control"] = "no-store"
    return await playlist_tracks(session, playlist_id, viewer, settings, limit, offset)


@router.post("/playlists/{playlist_id}/tracks", status_code=status.HTTP_204_NO_CONTENT)
async def add_track(
    playlist_id: EntityId,
    payload: PlaylistTrackAdd,
    session: SessionDependency,
    user: CurrentUserDependency,
):
    await change_tracks(session, playlist_id, user, "add", payload=payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/playlists/{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_track(
    playlist_id: EntityId,
    track_id: EntityId,
    session: SessionDependency,
    user: CurrentUserDependency,
):
    await change_tracks(session, playlist_id, user, "remove", track_id=track_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/playlists/{playlist_id}/tracks/order", status_code=status.HTTP_204_NO_CONTENT
)
async def reorder(
    playlist_id: EntityId,
    payload: PlaylistReorder,
    session: SessionDependency,
    user: CurrentUserDependency,
):
    await change_tracks(session, playlist_id, user, "reorder", payload=payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
