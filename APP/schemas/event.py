# APP/schemas/event.py
from pydantic import BaseModel
from datetime import datetime
from event_type import EventType
from venue import VenueShort
from city import CityOut

class EventOut(BaseModel):
    venue : VenueShort
    time : datetime
    typeEvent : list[EventType]


