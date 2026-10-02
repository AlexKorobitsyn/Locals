from typing import Annotated

from fastapi import APIRouter, Query, Response

from APP.core.config import SettingsDependency
from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import (
    CurrentUserDependency,
    OptionalUserDependency,
)
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.schemas.venue import VenueCreate, VenueOut, VenueRatedShort, VenueUpdate
from APP.services.places import change_venue, venue_detail, venues_page

router = APIRouter(prefix="/venues", tags=["venues"])


@router.post("", response_model=VenueOut, status_code=201)
async def create(
    payload: VenueCreate,
    session: SessionDependency,
    user: CurrentUserDependency,
    settings: SettingsDependency,
):
    return await change_venue(session, user, settings, payload)


@router.get("", response_model=Page[VenueRatedShort])
async def venues(
    session: SessionDependency,
    user: OptionalUserDependency,
    settings: SettingsDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    sort: str = "-created_at",
    city_id: Annotated[int | None, Query(gt=0)] = None,
    min_lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    max_lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    min_lng: Annotated[float | None, Query(ge=-180, le=180)] = None,
    max_lng: Annotated[float | None, Query(ge=-180, le=180)] = None,
):
    response.headers["Cache-Control"] = "no-store"
    return await venues_page(
        session,
        user,
        settings,
        limit,
        offset,
        sort,
        city_id=city_id,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lng=min_lng,
        max_lng=max_lng,
    )


@router.get("/{venue_id}", response_model=VenueOut)
async def detail(
    venue_id: EntityId,
    session: SessionDependency,
    user: OptionalUserDependency,
    settings: SettingsDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await venue_detail(session, venue_id, user, settings)


@router.patch("/{venue_id}", response_model=VenueOut)
async def update(
    venue_id: EntityId,
    payload: VenueUpdate,
    session: SessionDependency,
    user: CurrentUserDependency,
    settings: SettingsDependency,
):
    return await change_venue(session, user, settings, payload, venue_id)
