from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, computed_field

from APP.core.constants import (
    MAX_RATING,
    MIN_RATING,
    NAME_MAX_LENGTH,
    RATING_STEP,
)

MIN_LATITUDE = -90
MAX_LATITUDE = 90
MIN_LONGITUDE = -180
MAX_LONGITUDE = 180

PositiveInteger = Annotated[int, Field(gt=0, strict=True)]
PositiveId = PositiveInteger
NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_MAX_LENGTH),
]
NonNegativeInt = Annotated[int, Field(ge=0)]
RatingValue = Annotated[
    float,
    Field(
        ge=MIN_RATING,
        le=MAX_RATING,
        multiple_of=float(RATING_STEP),
        allow_inf_nan=False,
    ),
]
RatingAverage = Annotated[float, Field(ge=MIN_RATING, le=MAX_RATING)]
Latitude = Annotated[float, Field(ge=MIN_LATITUDE, le=MAX_LATITUDE)]
Longitude = Annotated[float, Field(ge=MIN_LONGITUDE, le=MAX_LONGITUDE)]


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class InputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RatingFields(BaseSchema):
    rating_sum: Decimal = Field(default=Decimal("0"), exclude=True, ge=0)
    rating_weight: Decimal = Field(default=Decimal("0"), exclude=True, ge=0)
    ratings_count: NonNegativeInt = 0
    my_rating: RatingValue | None = None
    likes_count: NonNegativeInt = 0
    is_liked_by_me: bool = False

    @computed_field
    @property
    def rating_avg(self) -> RatingAverage | None:
        if self.ratings_count == 0 or self.rating_weight == 0:
            return None
        return float(self.rating_sum / self.rating_weight)


class TimestampMixin(BaseSchema):
    created_at: datetime
