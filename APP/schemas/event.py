# APP/schemas/event.py
from common import BaseSchema
from datetime import datetime
from event_type import EventType
from venue import VenueShort
from city import CityOut

class EventOut(BaseSchema):
    id : int
    name : str
    venue : VenueShort
    starts_at : datetime
    stop_at : datetime = None # на случай если неизвестно когда закончится
    type_event : list[EventType]

class EventCreate(BaseSchema):
    name: str
    venue_id: int
    starts_at: datetime
    stop_at: datetime | None = None
    type_event_ids: list[int] = []

class EventUpdate(BaseSchema):
    name: str | None = None
    venue_id: int | None = None
    starts_at: datetime | None = None
    stop_at: datetime | None = None
    type_event_ids: list[int] | None = None

