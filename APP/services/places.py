from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import and_, exists, func, literal, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from APP.core.constants import DEFAULT_EVENT_TYPE_ID, PRIVILEGED_LEVELS
from APP.core.dependencies import require_owner_or_privileged
from APP.models.city import City
from APP.models.event import Event
from APP.models.event_attendance import EventAttendance
from APP.models.event_type import EventType
from APP.models.venue import Venue
from APP.schemas.city import CityOut
from APP.schemas.event import EventOut
from APP.schemas.event_type import EventType as EventTypeOut
from APP.schemas.pagination import Page
from APP.schemas.venue import VenueOut, VenueRatedShort
from APP.services.activity import record_event
from APP.services.catalog import related_rows, scalar_values
from APP.services.contributions import enforce_contribution_limit, submit_publication
from APP.services.engagement import set_engagement, with_engagement
from APP.services.experience import experience_output
from APP.services.ratings import (
    lock_user,
    rating_average_expression,
    set_rating_context,
    with_my_rating,
)


def location_filters(
    model, city_id=None, min_lat=None, max_lat=None, min_lng=None, max_lng=None
):
    filters = []
    if city_id is not None:
        filters.append(model.city_id == city_id)
    values = (min_lat, max_lat, min_lng, max_lng)
    if any(value is not None for value in values):
        if (
            any(value is None for value in values)
            or min_lat > max_lat
            or min_lng > max_lng
        ):
            raise HTTPException(
                status_code=422, detail="Provide a valid complete bounding box"
            )
        filters.extend(
            [model.lat.between(min_lat, max_lat), model.lng.between(min_lng, max_lng)]
        )
    return filters


async def city_page(session, limit, offset, q=None):
    filters = []
    if q:
        # autoescape не превращает пользовательский текст в шаблон LIKE.
        filters.append(City.name.icontains(q, autoescape=True))
    rows = list(
        (
            await session.scalars(
                select(City)
                .where(*filters)
                .order_by(City.name, City.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    total = await session.scalar(select(func.count()).select_from(City).where(*filters))
    return Page(
        items=[CityOut.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


async def create_city(session, payload, user):
    try:
        async with session.begin():
            city = City(**payload.model_dump())
            session.add(city)
            await session.flush()
            record_event(
                session, user.id, "city_created", "city", city.id, public=False
            )
            output = CityOut.model_validate(city)
        return output
    except IntegrityError as exc:
        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise HTTPException(status_code=409, detail="City already exists") from None
        raise


async def city_detail(session, city_id):
    city = await session.get(City, city_id)
    if city is None:
        raise HTTPException(status_code=404, detail="City not found")
    return CityOut.model_validate(city)


def venue_query(viewer):
    count = (
        select(func.count())
        .select_from(Event)
        .where(Event.venue_id == Venue.id, Event.publication_status == "published")
        .correlate(Venue)
        .scalar_subquery()
        .label("events_count")
    )
    return with_engagement(
        with_my_rating(
            select(Venue, count).options(selectinload(Venue.city)),
            Venue,
            "venue",
            viewer,
        ),
        Venue,
        "venue",
        viewer,
    )


def venue_output(row, viewer, settings, details=True):
    output = (VenueOut if details else VenueRatedShort).model_validate(row.Venue)
    if details:
        output.events_count = row.events_count
        output.is_owner = viewer is not None and viewer.id == row.Venue.user_id
    return set_engagement(set_rating_context(output, row.my_rating, settings), row)


async def venue_detail(session, venue_id, viewer, settings):
    row = (
        await session.execute(
            venue_query(viewer)
            .where(Venue.id == venue_id)
            .execution_options(populate_existing=True)
        )
    ).one_or_none()
    if row is None or (
        row.Venue.publication_status != "published"
        and (
            viewer is None
            or (
                viewer.id != row.Venue.user_id and viewer.level not in PRIVILEGED_LEVELS
            )
        )
    ):
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue_output(row, viewer, settings)


async def venues_page(session, viewer, settings, limit, offset, sort, **location):
    filters = [
        Venue.publication_status == "published",
        *location_filters(Venue, **location),
    ]
    fields = {
        "id": Venue.id,
        "name": Venue.name,
        "created_at": Venue.created_at,
        "rating_avg": rating_average_expression(Venue, settings),
        "ratings_count": Venue.ratings_count,
    }
    ordering = allowed_sort(fields, sort, Venue.id)
    rows = (
        await session.execute(
            venue_query(viewer)
            .where(*filters)
            .order_by(*ordering)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    total = await session.scalar(
        select(func.count()).select_from(Venue).where(*filters)
    )
    return Page(
        items=[venue_output(row, viewer, settings, details=False) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def allowed_sort(fields, sort, id_column):
    name = sort.removeprefix("-")
    name = {"createdAt": "created_at", "startsAt": "starts_at"}.get(name, name)
    if name not in fields:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sort; allowed: {', '.join(sorted(fields))}",
        )
    column = fields[name]
    descending = sort.startswith("-")
    return [
        (column.desc() if descending else column.asc()).nulls_last(),
        id_column.desc() if descending else id_column.asc(),
    ]


async def change_venue(session, user, settings, payload, venue_id=None):
    async with session.begin():
        current = await lock_user(session, user.id)
        if venue_id is None or "city_id" in payload.model_fields_set:
            if await session.get(City, payload.city_id) is None:
                raise HTTPException(status_code=404, detail="City not found")
        if venue_id is None:
            status = (
                "published"
                if current.scene_verified or current.level in PRIVILEGED_LEVELS
                else "pending"
            )
            if status == "pending":
                await enforce_contribution_limit(session, current, settings)
            venue = Venue(
                user_id=user.id,
                publication_status=status,
                **scalar_values(payload, set()),
            )
            session.add(venue)
        else:
            venue = await session.scalar(
                select(Venue).where(Venue.id == venue_id).with_for_update()
            )
            if venue is None:
                raise HTTPException(status_code=404, detail="Venue not found")
            require_owner_or_privileged(venue.user_id, user)
            if venue.publication_status != "published":
                raise HTTPException(
                    status_code=409,
                    detail="Withdraw the pending proposal and create a corrected one",
                )
            for key, value in scalar_values(payload, set()).items():
                setattr(venue, key, value)
                if key == "cover_url":
                    venue.image_media_id = None
        await session.flush()
        if venue_id is None and venue.publication_status == "pending":
            await submit_publication(session, current, venue, "venue", settings)
        record_event(
            session,
            user.id,
            "venue_created" if venue_id is None else "venue_updated",
            "venue",
            venue.id,
            public=venue.publication_status == "published",
        )
        output = await venue_detail(session, venue.id, user, settings)
    return output


def event_query(viewer):
    return with_engagement(
        select(Event)
        .add_columns(
            select(func.count())
            .select_from(EventAttendance)
            .where(EventAttendance.event_id == Event.id)
            .correlate(Event)
            .scalar_subquery()
            .label("attendees_count"),
            (
                exists()
                .where(
                    EventAttendance.event_id == Event.id,
                    EventAttendance.user_id == viewer.id,
                )
                .correlate(Event)
                if viewer is not None
                else literal(False)
            ).label("is_going_by_me"),
        )
        .options(
            selectinload(Event.city),
            selectinload(Event.venue).selectinload(Venue.city),
            selectinload(Event.type_event),
        ),
        Event,
        "event",
        viewer,
    )


def event_output(row, viewer):
    output = EventOut.model_validate(row.Event)
    if output.venue is not None:
        # Привязанное событие следует за актуальным местоположением площадки.
        output.lat, output.lng, output.city = (
            output.venue.lat,
            output.venue.lng,
            output.venue.city,
        )
    output.is_owner = viewer is not None and viewer.id == row.Event.user_id
    output.attendees_count = row.attendees_count
    output.is_going_by_me = row.is_going_by_me
    return set_engagement(output, row)


async def event_detail(session, event_id, viewer):
    row = (
        await session.execute(
            event_query(viewer)
            .where(Event.id == event_id)
            .execution_options(populate_existing=True)
        )
    ).one_or_none()
    if row is None or (
        row.Event.publication_status != "published"
        and (
            viewer is None
            or (
                viewer.id != row.Event.user_id and viewer.level not in PRIVILEGED_LEVELS
            )
        )
    ):
        raise HTTPException(status_code=404, detail="Event not found")
    return event_output(row, viewer)


async def events_page(
    session,
    viewer,
    limit,
    offset,
    sort,
    starts_after=None,
    starts_before=None,
    type_event_id=None,
    venue_id=None,
    **location,
):
    filters = [Event.publication_status == "published"]
    event_location = location_filters(Event, **location)
    if event_location:
        filters.append(
            or_(
                and_(Event.venue_id.is_(None), *event_location),
                Event.venue.has(and_(*location_filters(Venue, **location))),
            )
        )
    if venue_id is not None:
        filters.append(Event.venue_id == venue_id)
    if (
        starts_after is not None
        and starts_before is not None
        and starts_after > starts_before
    ):
        raise HTTPException(status_code=422, detail="Invalid date range")
    if starts_after is not None:
        filters.append(Event.starts_at >= starts_after)
    if starts_before is not None:
        filters.append(Event.starts_at <= starts_before)
    if type_event_id is not None:
        filters.append(Event.type_event.any(EventType.id == type_event_id))
    fields = {
        "id": Event.id,
        "name": Event.name,
        "starts_at": Event.starts_at,
        "created_at": Event.created_at,
    }
    rows = (
        await session.execute(
            event_query(viewer)
            .where(*filters)
            .order_by(*allowed_sort(fields, sort, Event.id))
            .limit(limit)
            .offset(offset)
        )
    ).all()
    total = await session.scalar(
        select(func.count()).select_from(Event).where(*filters)
    )
    return Page(
        items=[event_output(row, viewer) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


async def change_event(session, user, payload, event_id=None):
    async with session.begin():
        current = await lock_user(session, user.id)
        settings = session.info["settings"]
        if event_id is None:
            active = await session.scalar(
                select(func.count())
                .select_from(Event)
                .where(
                    Event.user_id == user.id,
                    Event.starts_at > datetime.now(UTC),
                    Event.publication_status != "rejected",
                )
            )
            if (
                current.level not in PRIVILEGED_LEVELS
                and active >= experience_output(current, settings).event_limit
            ):
                raise HTTPException(
                    status_code=409, detail="Active event limit reached"
                )
            status = (
                "published"
                if current.scene_verified or current.level in PRIVILEGED_LEVELS
                else "pending"
            )
            if status == "pending":
                await enforce_contribution_limit(session, current, settings)
            event = Event(user_id=user.id, publication_status=status)
            session.add(event)
            fields = payload.model_fields_set | {
                "venue_id",
                "city_id",
                "lat",
                "lng",
                "type_event_ids",
            }
        else:
            event = await session.scalar(
                select(Event)
                .where(Event.id == event_id)
                .options(selectinload(Event.type_event))
                .with_for_update()
            )
            if event is None:
                raise HTTPException(status_code=404, detail="Event not found")
            require_owner_or_privileged(event.user_id, user)
            if event.publication_status != "published":
                raise HTTPException(
                    status_code=409,
                    detail="Withdraw the pending proposal and create a corrected one",
                )
            fields = payload.model_fields_set
            if (
                "starts_at" in fields
                and payload.starts_at > datetime.now(UTC)
                and event.starts_at <= datetime.now(UTC)
                and current.level not in PRIVILEGED_LEVELS
            ):
                active = await session.scalar(
                    select(func.count())
                    .select_from(Event)
                    .where(
                        Event.user_id == user.id,
                        Event.starts_at > datetime.now(UTC),
                        Event.publication_status != "rejected",
                    )
                )
                if active >= experience_output(current, settings).event_limit:
                    raise HTTPException(
                        status_code=409, detail="Active event limit reached"
                    )
        # Не flush-им новый Event до заполнения обязательных координат и времени.
        with session.no_autoflush:
            venue_id = payload.venue_id if "venue_id" in fields else event.venue_id
            venue = await session.get(Venue, venue_id) if venue_id is not None else None
            if venue_id is not None and (
                venue is None
                or (
                    venue.publication_status != "published"
                    and venue.user_id != user.id
                    and user.level not in PRIVILEGED_LEVELS
                )
            ):
                raise HTTPException(status_code=404, detail="Venue not found")
            if (
                venue is not None
                and venue.publication_status != "published"
                and event.publication_status == "published"
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Publish the venue before publishing its events",
                )
            city_id = payload.city_id if "city_id" in fields else event.city_id
            if venue is not None:
                if "city_id" in payload.model_fields_set and city_id != venue.city_id:
                    raise HTTPException(
                        status_code=422, detail="Event city must match venue city"
                    )
                city_id = venue.city_id
            if city_id is None:
                raise HTTPException(
                    status_code=422, detail="A city or venue is required"
                )
            city = await session.get(City, city_id)
            if city is None:
                raise HTTPException(status_code=404, detail="City not found")
            event.city_id, event.venue_id = city_id, venue_id
            for coordinate in ("lat", "lng"):
                provided = (
                    getattr(payload, coordinate)
                    if coordinate in fields
                    else getattr(event, coordinate)
                )
                if provided is None or (
                    "venue_id" in fields and coordinate not in payload.model_fields_set
                ):
                    provided = getattr(venue if venue is not None else city, coordinate)
                setattr(event, coordinate, provided)
            if "type_event_ids" in fields:
                ids = payload.type_event_ids
                if not ids:
                    if event_id is not None:
                        raise HTTPException(
                            status_code=422,
                            detail="At least one event type is required",
                        )
                    ids = [DEFAULT_EVENT_TYPE_ID]
                if len(ids) != len(set(ids)):
                    raise HTTPException(
                        status_code=422, detail="Event types must be unique"
                    )
                event.type_event = await related_rows(session, EventType, ids)
            for key, value in scalar_values(
                payload, {"city_id", "venue_id", "lat", "lng", "type_event_ids"}
            ).items():
                setattr(event, key, value)
            if event.stop_at is not None and event.stop_at <= event.starts_at:
                raise HTTPException(
                    status_code=422, detail="stop_at must be later than starts_at"
                )
        await session.flush()
        if event_id is None and event.publication_status == "pending":
            await submit_publication(session, current, event, "event", settings)
        record_event(
            session,
            user.id,
            "event_created" if event_id is None else "event_updated",
            "event",
            event.id,
            public=event.publication_status == "published",
        )
        output = await event_detail(session, event.id, user)
    return output


async def delete_event(session, user, event_id):
    async with session.begin():
        await lock_user(session, user.id)
        event = await session.scalar(
            select(Event).where(Event.id == event_id).with_for_update()
        )
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        require_owner_or_privileged(event.user_id, user)
        record_event(session, user.id, "event_deleted", "event", event.id)
        await session.delete(event)


async def event_types(session):
    return [
        EventTypeOut.model_validate(row)
        for row in (
            await session.scalars(select(EventType).order_by(EventType.id))
        ).all()
    ]


async def set_attendance(session, actor, event_id, remove=False):
    from APP.models.event_attendance import EventAttendance

    async with session.begin():
        await lock_user(session, actor.id)
        event = await session.scalar(
            select(Event)
            .where(Event.id == event_id, Event.publication_status == "published")
            .with_for_update(read=True, key_share=True)
        )
        if event is None:
            raise HTTPException(status_code=404, detail="Published event not found")
        attendance = await session.get(EventAttendance, (event_id, actor.id))
        changed = False
        if remove and attendance is not None:
            await session.delete(attendance)
            changed = True
        elif not remove and attendance is None:
            session.add(EventAttendance(event_id=event_id, user_id=actor.id))
            changed = True
        if changed:
            record_event(
                session,
                actor.id,
                "event_attendance_removed" if remove else "event_attendance_added",
                "event",
                event_id,
            )
        await session.flush()
        output = await event_detail(session, event_id, actor)
    return output
