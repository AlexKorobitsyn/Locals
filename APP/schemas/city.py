# app/schemas/city.py
from pydantic import BaseModel


class CityShort(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class CityOut(BaseModel):
    id: int
    name: str
    region: str | None
    country: str
    lat: float
    lng: float
    timezone: str
    class Config:
        from_attributes = True