# app/schemas/city.py
from common import BaseSchema


class CityShort(BaseSchema):
    id: int
    name: str
    class Config:
        from_attributes = True

class CityOut(BaseSchema):
    id: int
    name: str
    region: str | None
    country: str
    lat: float
    lng: float
    timezone: str
    class Config:
        from_attributes = True