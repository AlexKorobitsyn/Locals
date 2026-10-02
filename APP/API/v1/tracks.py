from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from APP.core.config import SettingsDependency
from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import (
    CurrentUserDependency,
    OptionalUserDependency,
    PrivilegedUserDependency,
)
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.schemas.track import TrackCreate, TrackOut, TrackRatedShort, TrackUpdate
from APP.services.catalog import (
    create_track,
    delete_catalog,
    get_detail,
    list_catalog,
    update_catalog,
)

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.post("", response_model=TrackOut, status_code=status.HTTP_201_CREATED)
async def create(
    payload: TrackCreate,
    session: SessionDependency,
    user: CurrentUserDependency,
    settings: SettingsDependency,
):
    return await create_track(session, payload, user, settings)


@router.get("", response_model=Page[TrackRatedShort], openapi_extra={"security": [{}]})
async def list_tracks(
    session: SessionDependency,
    viewer: OptionalUserDependency,
    response: Response,
    settings: SettingsDependency,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    sort: str = "-created_at",
    artist_id: Annotated[int | None, Query(gt=0)] = None,
    album_id: Annotated[int | None, Query(gt=0)] = None,
):
    response.headers["Cache-Control"] = "no-store"
    return await list_catalog(
        session,
        "track",
        viewer,
        limit,
        offset,
        sort,
        settings,
        artist_id=artist_id,
        album_id=album_id,
    )


@router.get("/{track_id}", response_model=TrackOut, openapi_extra={"security": [{}]})
async def detail(
    track_id: EntityId,
    session: SessionDependency,
    viewer: OptionalUserDependency,
    response: Response,
    settings: SettingsDependency,
):
    response.headers["Cache-Control"] = "no-store"
    return await get_detail(session, "track", track_id, viewer, settings)


@router.patch("/{track_id}", response_model=TrackOut)
async def update(
    track_id: EntityId,
    payload: TrackUpdate,
    session: SessionDependency,
    user: CurrentUserDependency,
    settings: SettingsDependency,
):
    return await update_catalog(session, "track", track_id, payload, user, settings)


@router.delete("/{track_id}", status_code=204)
async def remove(
    track_id: EntityId, session: SessionDependency, user: PrivilegedUserDependency
):
    await delete_catalog(session, "track", track_id, user)
