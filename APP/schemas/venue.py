from pydantic import AnyHttpUrl, Field, field_validator

from APP.core.constants import DESCRIPTION_MAX_LENGTH, MAX_DATABASE_INTEGER
from APP.schemas.city import CityShort
from APP.schemas.common import (
    BaseSchema,
    InputSchema,
    Latitude,
    Longitude,
    NonEmptyText,
    NonNegativeInt,
    PositiveId,
    RatingFields,
)


class VenueShort(BaseSchema):
    id: int
    name: str
    cover_url: str | None = None
    city: CityShort


class VenueRatedShort(VenueShort, RatingFields):
    pass


class VenueOut(VenueRatedShort):
    description: str | None = None
    address: str | None = None
    lat: Latitude
    lng: Longitude
    capacity: NonNegativeInt | None = None
    website: str | None = None
    events_count: NonNegativeInt = 0
    followers_count: NonNegativeInt = 0
    user_id: int | None = None
    is_owner: bool = False
    is_liked_by_me: bool = False
    is_followed_by_me: bool = False


class VenueCreate(InputSchema):
    name: NonEmptyText
    city_id: PositiveId
    lat: Latitude
    lng: Longitude
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    address: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    capacity: int | None = Field(default=None, ge=0, le=MAX_DATABASE_INTEGER)
    website: AnyHttpUrl | None = None
    cover_url: AnyHttpUrl | None = None


class VenueUpdate(InputSchema):
    name: NonEmptyText | None = None
    city_id: PositiveId | None = None
    lat: Latitude | None = None
    lng: Longitude | None = None
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    address: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    capacity: int | None = Field(default=None, ge=0, le=MAX_DATABASE_INTEGER)
    website: AnyHttpUrl | None = None
    cover_url: AnyHttpUrl | None = None

    @field_validator("name", "city_id", "lat", "lng")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("field cannot be null")
        return value
