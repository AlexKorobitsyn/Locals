from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from APP.core.constants import EXPERIENCE_TIER_COUNT
from APP.schemas.common import BaseSchema, InputSchema


class ExperienceOut(BaseSchema):
    experience_points: int = Field(ge=0)
    experience_tier: int = Field(ge=0, le=EXPERIENCE_TIER_COUNT)
    experience_level: int = Field(ge=1, le=9)
    level_name: str
    rating_weight: float = Field(gt=0)
    rating_level_weights: list[float] = Field(min_length=9, max_length=9)
    thresholds: list[int]
    contribution_limit: int
    event_limit: int
    votes_required: int
    micro_daily_cap: int
    review_daily_cap: int
    review_points: int
    milestone_points: int
    next_threshold: int | None
    lyrics_threshold: int
    genres_threshold: int
    scene_threshold: int
    listen_daily_cap: int
    quality_track_points: int
    quality_min_raters: int
    quality_min_rating: float


class ExperienceTierPut(InputSchema):
    tier: Annotated[int, Field(strict=True, ge=0, le=EXPERIENCE_TIER_COUNT)]


class ListeningOut(BaseSchema):
    id: UUID
    seconds: float
    required_seconds: float
    awarded: bool = False
    experience: ExperienceOut


class ListeningHeartbeat(InputSchema):
    is_playing: bool = Field(strict=True)


class ExperienceAwardOut(BaseSchema):
    id: int
    kind: str
    points: int
    day: date
    created_at: datetime


class CommunityAwardCreate(InputSchema):
    kind: Literal["curator_week", "reviewer_month"]
    period: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
