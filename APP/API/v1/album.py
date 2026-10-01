from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from APP.core.config import SettingsDependency
from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency, OptionalUserDependency
from APP.schemas.album import AlbumCreate, AlbumOut, AlbumRatedShort, AlbumUpdate
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.services.catalog import create_album, get_detail, list_catalog, update_catalog

router = APIRouter(prefix="/albums", tags=["albums"])


@router.post("", response_model=AlbumOut, status_code=status.HTTP_201_CREATED)
async def create(
    payload: AlbumCreate,
    session: SessionDependency,
    user: CurrentUserDependency,
    settings: SettingsDependency,
):
    return await create_album(session, payload, user, settings)


@router.get("", response_model=Page[AlbumRatedShort], openapi_extra={"security": [{}]})
async def list_albums(
    session: SessionDependency,
    viewer: OptionalUserDependency,
    response: Response,
    settings: SettingsDependency,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    sort: str = "-created_at",
    artist_id: Annotated[int | None, Query(gt=0)] = None,
):
    response.headers["Cache-Control"] = "no-store"
    return await list_catalog(
        session, "album", viewer, limit, offset, sort, settings, artist_id=artist_id
    )


@router.get("/{album_id}", response_model=AlbumOut, openapi_extra={"security": [{}]})
async def detail(
    album_id: EntityId,
    session: SessionDependency,
    viewer: OptionalUserDependency,
    response: Response,
    settings: SettingsDependency,
):
    response.headers["Cache-Control"] = "no-store"
    return await get_detail(session, "album", album_id, viewer, settings)


@router.patch("/{album_id}", response_model=AlbumOut)
async def update(
    album_id: EntityId,
    payload: AlbumUpdate,
    session: SessionDependency,
    user: CurrentUserDependency,
    settings: SettingsDependency,
):
    return await update_catalog(session, "album", album_id, payload, user, settings)
