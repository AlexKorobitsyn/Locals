from fastapi import APIRouter, Response

from APP.core.config import SettingsDependency
from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency
from APP.schemas.album import AlbumRatedShort
from APP.schemas.artist import ArtistRatedShort
from APP.schemas.pagination import Page, PageLimit, PageOffset
from APP.schemas.track import TrackRatedShort
from APP.services.catalog import list_catalog

router = APIRouter(prefix="/me", tags=["studio"])


@router.get("/artists", response_model=Page[ArtistRatedShort])
async def my_artists(
    session: SessionDependency,
    user: CurrentUserDependency,
    response: Response,
    settings: SettingsDependency,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    sort: str = "-created_at",
):
    response.headers["Cache-Control"] = "no-store"
    return await list_catalog(
        session, "artist", user, limit, offset, sort, settings, owner_id=user.id
    )


@router.get("/albums", response_model=Page[AlbumRatedShort])
async def my_albums(
    session: SessionDependency,
    user: CurrentUserDependency,
    response: Response,
    settings: SettingsDependency,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    sort: str = "-created_at",
):
    response.headers["Cache-Control"] = "no-store"
    return await list_catalog(
        session, "album", user, limit, offset, sort, settings, owner_id=user.id
    )


@router.get("/tracks", response_model=Page[TrackRatedShort])
async def my_tracks(
    session: SessionDependency,
    user: CurrentUserDependency,
    response: Response,
    settings: SettingsDependency,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    sort: str = "-created_at",
):
    response.headers["Cache-Control"] = "no-store"
    return await list_catalog(
        session, "track", user, limit, offset, sort, settings, owner_id=user.id
    )
