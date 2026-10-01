from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator

from APP.core.constants import NAME_MAX_LENGTH, ROLE_MAX_LENGTH
from APP.schemas.common import (
    BaseSchema,
    InputSchema,
    Latitude,
    Longitude,
    NonEmptyText,
)


class CityShort(BaseSchema):
    id: int
    name: str


class CityOut(CityShort):
    region: str | None = None
    country: str
    lat: Latitude
    lng: Longitude
    timezone: str


class CityCreate(InputSchema):
    name: NonEmptyText
    region: str | None = Field(default=None, max_length=NAME_MAX_LENGTH)
    country: NonEmptyText
    lat: Latitude
    lng: Longitude
    timezone: str = Field(max_length=ROLE_MAX_LENGTH)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ValueError, ZoneInfoNotFoundError):
            raise ValueError("unknown IANA timezone") from None
        return value
