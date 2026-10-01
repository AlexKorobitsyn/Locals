from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator

from APP.core.constants import NAME_MAX_LENGTH, REVIEW_MAX_LENGTH, RatingTarget
from APP.schemas.common import (
    BaseSchema,
    InputSchema,
    NonNegativeInt,
    PositiveId,
    RatingAverage,
)
from APP.schemas.user import UserShort


class ReviewShort(BaseSchema):
    id: int
    title: str | None = None
    rating: RatingAverage
    likes_count: NonNegativeInt = 0
    created_at: datetime


class ReviewOut(ReviewShort):
    text: str
    author: UserShort
    target_type: Literal["track", "album", "artist", "venue"]
    target_id: int
    is_liked_by_me: bool = False
    is_owner: bool = False
    updated_at: datetime


ReviewText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=1, max_length=REVIEW_MAX_LENGTH
    ),
]


class ReviewCreate(InputSchema):
    target_type: RatingTarget
    target_id: PositiveId
    title: str | None = Field(default=None, max_length=NAME_MAX_LENGTH)
    text: ReviewText


class ReviewUpdate(InputSchema):
    title: str | None = Field(default=None, max_length=NAME_MAX_LENGTH)
    text: ReviewText | None = None

    @field_validator("text")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("text cannot be null")
        return value
