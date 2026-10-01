from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator

from APP.core.constants import MAX_RATING, MIN_RATING, RATING_STEP, RatingTarget
from APP.schemas.common import InputSchema, NonNegativeInt, PositiveId, RatingFields


class RatingPut(InputSchema):
    target_type: RatingTarget
    target_id: PositiveId
    value: Annotated[
        Decimal,
        Field(
            ge=MIN_RATING,
            le=MAX_RATING,
            multiple_of=Decimal(RATING_STEP),
            max_digits=2,
            decimal_places=1,
            allow_inf_nan=False,
        ),
    ]

    @field_validator("value", mode="before", json_schema_input_type=float)
    @classmethod
    def require_number(cls, value):
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
            raise ValueError("value must be a number")
        return value


class RatingResult(RatingFields):
    target_type: RatingTarget
    target_id: int
    likes_count: NonNegativeInt = Field(default=0, exclude=True)
    is_liked_by_me: bool = Field(default=False, exclude=True)
