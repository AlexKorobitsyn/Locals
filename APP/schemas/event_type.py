# APP/schemas/event_type.py
from common import BaseSchema

class EventType(BaseSchema):
    id : int # тип из бд по id
    name : str # Джем
    slug : str # Для машины jam, в url
