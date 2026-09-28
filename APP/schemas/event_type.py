# APP/schemas/event_type.py
from pydantic import BaseModel

class EventType(BaseModel):
    id : int # тип из бд по id
    name : str # Джем
    slug : str # Для машины jam, в url
