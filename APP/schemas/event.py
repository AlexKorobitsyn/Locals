from datetime import datetime
from typing import Self

from pydantic import AwareDatetime, Field, field_validator, model_validator

from APP.core.constants import DESCRIPTION_MAX_LENGTH, MAX_RELATIONS
from APP.schemas.city import CityShort
from APP.schemas.common import (
    BaseSchema,
    InputSchema,
    Latitude,
    Longitude,
    NonEmptyText,
    NonNegativeInt,
    PositiveId,
)
from APP.schemas.event_type import EventType
from APP.schemas.venue import VenueShort


class EventOut(BaseSchema):
    id: int
    name: str
    venue: VenueShort | None = None
    starts_at: datetime
    stop_at: datetime | None = None
    type_event: list[EventType] = Field(default_factory=list)
    city: CityShort | None = None
    lat: Latitude | None = None
    lng: Longitude | None = None
    description: str | None = None
    user_id: int | None = None
    is_owner: bool = False
    is_liked_by_me: bool = False
    likes_count: NonNegativeInt = 0


class EventCreate(InputSchema):
    name: NonEmptyText
    venue_id: PositiveId | None = None
    city_id: PositiveId | None = None
    lat: Latitude | None = None
    lng: Longitude | None = None
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    starts_at: AwareDatetime
    stop_at: AwareDatetime | None = None
    type_event_ids: list[PositiveId] = Field(
        default_factory=list, max_length=MAX_RELATIONS
    )

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        if self.stop_at is not None and self.stop_at <= self.starts_at:
            raise ValueError("stop_at must be later than starts_at")
        return self


class EventUpdate(InputSchema):
    name: NonEmptyText | None = None
    venue_id: PositiveId | None = None
    city_id: PositiveId | None = None
    lat: Latitude | None = None
    lng: Longitude | None = None
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    starts_at: AwareDatetime | None = None
    stop_at: AwareDatetime | None = None
    type_event_ids: list[PositiveId] | None = Field(
        default=None, max_length=MAX_RELATIONS
    )

    @field_validator("name", "city_id", "lat", "lng", "starts_at", "type_event_ids")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field cannot be null; omit it to keep the current value")
        return value

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        # При частичном обновлении сравнение с сохранённой датой выполняет сервис.
        if (
            self.starts_at is not None
            and self.stop_at is not None
            and self.stop_at <= self.starts_at
        ):
            raise ValueError("stop_at must be later than starts_at")
        return self
