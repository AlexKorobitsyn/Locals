from typing import Literal

from pydantic import Field

from APP.schemas.artist import ArtistShort
from APP.schemas.common import BaseSchema
from APP.schemas.genre import GenreOut
from APP.schemas.pagination import Page
from APP.schemas.track import TrackRatedShort


class GenrePreference(BaseSchema):
    genre: GenreOut
    affinity: float = Field(ge=-2, le=2)
    ratings_count: int = Field(gt=0)


class RecommendationScore(BaseSchema):
    favorite_genre_score: float = Field(ge=0)
    rated_genre_score: float
    quality_score: float = Field(ge=0)
    total: float


class RecommendedTrack(TrackRatedShort):
    artists: list[ArtistShort] = Field(default_factory=list)
    genres: list[GenreOut] = Field(default_factory=list)
    is_playable: bool = False
    matched_favorite_genres: list[GenreOut] = Field(default_factory=list)
    genre_preferences: list[GenrePreference] = Field(default_factory=list)
    score: RecommendationScore
    reasons: list[
        Literal[
            "favorite_genres",
            "high_rated_genres",
            "low_rated_genres",
            "community_rating",
            "catalog_fallback",
        ]
    ]


class RecommendationPage(Page[RecommendedTrack]):
    mode: Literal["popular", "personalized"]
    algorithm_version: Literal["rules_v1"] = "rules_v1"
