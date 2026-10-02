from decimal import Decimal
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends, Request
from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from APP.core.constants import (
    DEFAULT_CONTRIBUTION_LIMITS,
    DEFAULT_CONTRIBUTION_VOTES,
    DEFAULT_EVENT_LIMIT,
    DEFAULT_EXPERIENCE_GENRES_POINTS,
    DEFAULT_EXPERIENCE_HIGHER_THRESHOLDS,
    DEFAULT_EXPERIENCE_LYRICS_POINTS,
    DEFAULT_EXPERIENCE_SCENE_POINTS,
    DEFAULT_LEGEND_EVENT_LIMIT,
    DEFAULT_LISTEN_DAILY_CAP,
    DEFAULT_MICRO_DAILY_CAP,
    DEFAULT_MILESTONE_POINTS,
    DEFAULT_QUALITY_MIN_RATERS,
    DEFAULT_QUALITY_MIN_RATING,
    DEFAULT_QUALITY_TRACK_POINTS,
    DEFAULT_RATING_PRIOR_MEAN,
    DEFAULT_RATING_PRIOR_STRENGTH,
    DEFAULT_RATING_WEIGHT_GREEN,
    DEFAULT_RATING_WEIGHT_PRIVILEGED,
    DEFAULT_RECOMMENDATION_FAVORITE_WEIGHT,
    DEFAULT_RECOMMENDATION_QUALITY_WEIGHT,
    DEFAULT_RECOMMENDATION_RATED_WEIGHT,
    DEFAULT_REVIEW_DAILY_CAP,
    DEFAULT_REVIEW_POINTS,
    JWT_SECRET_MIN_LENGTH,
    MAX_BCRYPT_ROUNDS,
    MAX_RATING,
    MIN_BCRYPT_ROUNDS,
    MIN_RATING,
)

MAX_PORT = 65535


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_name: str = "Music Service"
    port: int = Field(default=8000, gt=0, le=MAX_PORT)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: SecretStr
    db_pool_size: int = Field(default=5, gt=0)
    db_max_overflow: int = Field(default=10, ge=0)
    db_pool_timeout_seconds: float = Field(default=5.0, gt=0)
    db_connect_timeout_seconds: float = Field(default=5.0, gt=0)
    db_command_timeout_seconds: float = Field(default=30.0, gt=0)
    health_timeout_seconds: float = Field(default=3.0, gt=0)
    shutdown_timeout_seconds: int = Field(default=10, gt=0)
    jwt_secret_key: SecretStr = Field(min_length=JWT_SECRET_MIN_LENGTH)
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_issuer: str = "music-service"
    jwt_audience: str = "music-service-api"
    access_token_ttl_minutes: int = Field(default=15, gt=0)
    refresh_token_ttl_days: int = Field(default=30, gt=0)
    browser_allowed_origins: list[AnyHttpUrl] = Field(default_factory=list)
    browser_cookie_secure: bool = True
    bcrypt_rounds: int = Field(default=12, ge=MIN_BCRYPT_ROUNDS, le=MAX_BCRYPT_ROUNDS)
    experience_lyrics_points: int = Field(
        default=DEFAULT_EXPERIENCE_LYRICS_POINTS, gt=0
    )
    experience_genres_points: int = Field(
        default=DEFAULT_EXPERIENCE_GENRES_POINTS, gt=0
    )
    experience_scene_points: int = Field(default=DEFAULT_EXPERIENCE_SCENE_POINTS, gt=0)
    listen_daily_cap: int = Field(default=DEFAULT_LISTEN_DAILY_CAP, gt=0)
    quality_track_points: int = Field(default=DEFAULT_QUALITY_TRACK_POINTS, gt=0)
    quality_min_raters: int = Field(default=DEFAULT_QUALITY_MIN_RATERS, ge=2)
    quality_min_rating: Decimal = Field(
        default=Decimal(DEFAULT_QUALITY_MIN_RATING), ge=MIN_RATING, le=MAX_RATING
    )

    experience_higher_thresholds: list[int] = Field(
        default_factory=lambda: list(DEFAULT_EXPERIENCE_HIGHER_THRESHOLDS),
        min_length=5,
        max_length=5,
    )
    contribution_limits: list[int] = Field(
        default_factory=lambda: list(DEFAULT_CONTRIBUTION_LIMITS),
        min_length=9,
        max_length=9,
    )
    contribution_votes_required: int = Field(default=DEFAULT_CONTRIBUTION_VOTES, ge=2)
    event_active_limit: int = Field(default=DEFAULT_EVENT_LIMIT, gt=0)
    event_legend_limit: int = Field(default=DEFAULT_LEGEND_EVENT_LIMIT, gt=0)
    micro_daily_cap: int = Field(default=DEFAULT_MICRO_DAILY_CAP, gt=0)
    review_daily_cap: int = Field(default=DEFAULT_REVIEW_DAILY_CAP, gt=0)
    review_points: int = Field(default=DEFAULT_REVIEW_POINTS, gt=0)
    milestone_points: int = Field(default=DEFAULT_MILESTONE_POINTS, gt=0)

    @model_validator(mode="after")
    def validate_experience_thresholds(self):
        values = [
            self.experience_lyrics_points,
            self.experience_genres_points,
            self.experience_scene_points,
            *self.experience_higher_thresholds,
        ]
        if any(a >= b for a, b in zip(values, values[1:])):
            raise ValueError("Experience thresholds must be strictly increasing")
        if any(value <= 0 for value in self.contribution_limits) or any(
            a > b
            for a, b in zip(self.contribution_limits, self.contribution_limits[1:])
        ):
            raise ValueError("Contribution limits must be positive and nondecreasing")
        if self.event_legend_limit < self.event_active_limit:
            raise ValueError(
                "Legend event limit cannot be lower than the regular limit"
            )
        return self

    s3_endpoint_url: AnyHttpUrl | None = None
    s3_public_endpoint_url: AnyHttpUrl | None = None
    s3_access_key: SecretStr | None = None
    s3_secret_key: SecretStr | None = None
    s3_bucket: str = "music"
    s3_region: str = "us-east-1"
    s3_presign_ttl_seconds: int = Field(default=300, gt=0, le=604800)
    s3_connect_timeout_seconds: float = Field(default=3, gt=0)
    s3_read_timeout_seconds: float = Field(default=30, gt=0)
    s3_init_timeout_seconds: float = Field(default=60, gt=0)
    s3_cors_origins: list[str] = Field(default_factory=list)
    image_max_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    audio_max_bytes: int = Field(default=100 * 1024 * 1024, gt=0)
    image_max_pixels: int = Field(default=25_000_000, gt=0)

    @model_validator(mode="after")
    def storage_configuration(self):
        values = (self.s3_endpoint_url, self.s3_access_key, self.s3_secret_key)
        if any(v is not None for v in values) and not all(
            v is not None for v in values
        ):
            raise ValueError(
                "S3 endpoint and both credentials must be configured together"
            )
        if self.s3_public_endpoint_url is not None and self.s3_endpoint_url is None:
            raise ValueError("S3 public endpoint requires a storage endpoint")
        return self

    rating_prior_strength: Decimal = Field(
        default=Decimal(DEFAULT_RATING_PRIOR_STRENGTH),
        gt=0,
        max_digits=20,
        decimal_places=6,
    )
    rating_prior_mean: Decimal = Field(
        default=Decimal(DEFAULT_RATING_PRIOR_MEAN),
        ge=1,
        le=5,
        max_digits=20,
        decimal_places=6,
    )
    rating_weight_green: Decimal = Field(
        default=Decimal(DEFAULT_RATING_WEIGHT_GREEN),
        gt=0,
        max_digits=20,
        decimal_places=6,
    )
    rating_weight_experienced: Decimal = Field(
        default=Decimal(DEFAULT_RATING_WEIGHT_PRIVILEGED),
        gt=0,
        max_digits=20,
        decimal_places=6,
    )
    rating_weight_moderator: Decimal = Field(
        default=Decimal(DEFAULT_RATING_WEIGHT_PRIVILEGED),
        gt=0,
        max_digits=20,
        decimal_places=6,
    )
    rating_weight_admin: Decimal = Field(
        default=Decimal(DEFAULT_RATING_WEIGHT_PRIVILEGED),
        gt=0,
        max_digits=20,
        decimal_places=6,
    )

    recommendation_favorite_weight: Decimal = Field(
        default=Decimal(DEFAULT_RECOMMENDATION_FAVORITE_WEIGHT),
        ge=0,
        le=100,
        max_digits=10,
        decimal_places=6,
    )
    recommendation_rated_weight: Decimal = Field(
        default=Decimal(DEFAULT_RECOMMENDATION_RATED_WEIGHT),
        ge=0,
        le=100,
        max_digits=10,
        decimal_places=6,
    )
    recommendation_quality_weight: Decimal = Field(
        default=Decimal(DEFAULT_RECOMMENDATION_QUALITY_WEIGHT),
        gt=0,
        le=100,
        max_digits=10,
        decimal_places=6,
    )
    release_id: str = "dev"
    cors_origins: list[AnyHttpUrl] = Field(default_factory=list)

    @field_validator("cors_origins", "browser_allowed_origins")
    @classmethod
    def validate_origins(cls, values):
        for value in values:
            if (
                value.path not in (None, "", "/")
                or value.query
                or value.fragment
                or value.username
                or value.password
            ):
                raise ValueError(
                    "CORS origins must contain only a scheme, host and optional port"
                )
        return values

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
        except ArgumentError:
            raise ValueError("DATABASE_URL must be a valid PostgreSQL URL") from None
        if url.drivername != "postgresql+asyncpg":
            raise ValueError("DATABASE_URL must use the postgresql+asyncpg driver")
        if not url.database:
            raise ValueError("DATABASE_URL must include a database name")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


SettingsDependency = Annotated[Settings, Depends(get_app_settings)]
