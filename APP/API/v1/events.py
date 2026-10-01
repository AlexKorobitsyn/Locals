from typing import Annotated

from fastapi import APIRouter, Query, Response
from pydantic import AwareDatetime

from APP.core.constants import DEFAULT_PAGE_LIMIT
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency, OptionalUserDependency
from APP.schemas.event import EventCreate, EventOut, EventUpdate
from APP.schemas.event_type import EventType
from APP.schemas.pagination import EntityId, Page, PageLimit, PageOffset
from APP.services.places import (
    change_event,
    delete_event,
    event_detail,
    event_types,
    events_page,
)

router = APIRouter(tags=["events"])


@router.get("/event-types", response_model=list[EventType])
async def types(session: SessionDependency):
    return await event_types(session)


@router.post("/events", response_model=EventOut, status_code=201)
async def create(
    payload: EventCreate, session: SessionDependency, user: CurrentUserDependency
):
    return await change_event(session, user, payload)


@router.get("/events", response_model=Page[EventOut])
async def events(
    session: SessionDependency,
    user: OptionalUserDependency,
    response: Response,
    limit: PageLimit = DEFAULT_PAGE_LIMIT,
    offset: PageOffset = 0,
    sort: str = "starts_at",
    city_id: Annotated[int | None, Query(gt=0)] = None,
    min_lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    max_lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    min_lng: Annotated[float | None, Query(ge=-180, le=180)] = None,
    max_lng: Annotated[float | None, Query(ge=-180, le=180)] = None,
    starts_after: AwareDatetime | None = None,
    starts_before: AwareDatetime | None = None,
    type_event_id: Annotated[int | None, Query(gt=0)] = None,
):
    response.headers["Cache-Control"] = "no-store"
    return await events_page(
        session,
        user,
        limit,
        offset,
        sort,
        starts_after,
        starts_before,
        type_event_id,
        city_id=city_id,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lng=min_lng,
        max_lng=max_lng,
    )


@router.get("/events/{event_id}", response_model=EventOut)
async def detail(
    event_id: EntityId,
    session: SessionDependency,
    user: OptionalUserDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await event_detail(session, event_id, user)


@router.patch("/events/{event_id}", response_model=EventOut)
async def update(
    event_id: EntityId,
    payload: EventUpdate,
    session: SessionDependency,
    user: CurrentUserDependency,
):
    return await change_event(session, user, payload, event_id)


@router.delete("/events/{event_id}", status_code=204)
async def remove(
    event_id: EntityId, session: SessionDependency, user: CurrentUserDependency
):
    await delete_event(session, user, event_id)
