from fastapi import APIRouter, Response, status

from APP.core.config import SettingsDependency
from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency, OptionalUserDependency
from APP.schemas.artist import ArtistCreate, ArtistOut, ArtistRatedShort, ArtistUpdate
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.services.catalog import create_artist, get_detail, list_catalog, update_catalog

router = APIRouter(prefix="/artists", tags=["artists"])


@router.post("", response_model=ArtistOut, status_code=status.HTTP_201_CREATED)
async def create(
    payload: ArtistCreate,
    session: SessionDependency,
    user: CurrentUserDependency,
    settings: SettingsDependency,
):
    return await create_artist(session, payload, user, settings)


@router.get("", response_model=Page[ArtistRatedShort], openapi_extra={"security": [{}]})
async def list_artists(
    session: SessionDependency,
    viewer: OptionalUserDependency,
    response: Response,
    settings: SettingsDependency,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    sort: str = "-created_at",
):
    response.headers["Cache-Control"] = "no-store"
    return await list_catalog(session, "artist", viewer, limit, offset, sort, settings)


@router.get("/{artist_id}", response_model=ArtistOut, openapi_extra={"security": [{}]})
async def detail(
    artist_id: EntityId,
    session: SessionDependency,
    viewer: OptionalUserDependency,
    response: Response,
    settings: SettingsDependency,
):
    response.headers["Cache-Control"] = "no-store"
    return await get_detail(session, "artist", artist_id, viewer, settings)


@router.patch("/{artist_id}", response_model=ArtistOut)
async def update(
    artist_id: EntityId,
    payload: ArtistUpdate,
    session: SessionDependency,
    user: CurrentUserDependency,
    settings: SettingsDependency,
):
    return await update_catalog(session, "artist", artist_id, payload, user, settings)
