from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from APP.core.constants import LYRICS_MAX_LENGTH, MAX_RELATIONS
from APP.schemas.common import BaseSchema, InputSchema, PositiveId


class ContributionCreate(InputSchema):
    target_type: Literal["track", "album", "artist"]
    target_id: PositiveId
    field: Literal["lyrics", "genres", "metadata"]
    lyrics: str | None = Field(default=None, max_length=LYRICS_MAX_LENGTH)
    genre_ids: list[PositiveId] | None = Field(default=None, max_length=MAX_RELATIONS)

    name: str | None = Field(default=None, min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_values(self):
        if self.field == "metadata":
            if (
                self.name is None
                or not self.name.strip()
                or "lyrics" in self.model_fields_set
                or "genre_ids" in self.model_fields_set
            ):
                raise ValueError("Metadata corrections require a nonempty name only")
            self.name = self.name.strip()
            return self
        if "name" in self.model_fields_set:
            raise ValueError("name is only allowed for metadata")
        if self.field == "lyrics":
            if (
                self.target_type != "track"
                or "lyrics" not in self.model_fields_set
                or "genre_ids" in self.model_fields_set
            ):
                raise ValueError("lyrics changes require track and lyrics only")
        elif (
            self.genre_ids is None
            or "lyrics" in self.model_fields_set
            or len(set(self.genre_ids)) != len(self.genre_ids)
        ):
            raise ValueError("genres changes require unique genre_ids only")
        return self


class ContributionReview(InputSchema):
    decision: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=10000)


class ContributionOut(BaseSchema):
    id: int
    user_id: int
    reviewer_id: int | None
    target_type: str
    target_id: int
    field: str
    status: str
    before: dict
    proposed: dict
    reason: str | None
    created_at: datetime
    updated_at: datetime
    votes_count: int = 0
    eligible_votes_count: int = 0
    is_voted_by_me: bool = False
    requires_owner: bool = False
    can_review: bool = False
    can_approve: bool = False
