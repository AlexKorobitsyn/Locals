from datetime import date

from pydantic import AnyHttpUrl, Field, field_validator

from APP.core.constants import MAX_RELATIONS
from APP.schemas.artist import ArtistShort
from APP.schemas.common import (
    BaseSchema,
    InputSchema,
    NonEmptyText,
    NonNegativeInt,
    PositiveId,
    RatingFields,
)
from APP.schemas.genre import GenreOut


class AlbumShort(BaseSchema):
    id: int
    title: str
    cover_url: str | None = None
    release_date: date | None = None
    artists: list[ArtistShort] = Field(default_factory=list)


class AlbumRatedShort(AlbumShort, RatingFields):
    pass


class AlbumOut(AlbumRatedShort):
    genres: list[GenreOut] = Field(default_factory=list)
    tracks_count: NonNegativeInt = 0
    duration: NonNegativeInt = 0
    user_id: int | None = None
    is_owner: bool = False


class AlbumCreate(InputSchema):
    title: NonEmptyText
    cover_url: AnyHttpUrl | None = None
    release_date: date | None = None
    artist_ids: list[PositiveId] = Field(min_length=1, max_length=MAX_RELATIONS)
    genre_ids: list[PositiveId] = Field(default_factory=list, max_length=MAX_RELATIONS)

    @field_validator("artist_ids", "genre_ids")
    @classmethod
    def unique_ids(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("IDs must be unique")
        return value


class AlbumUpdate(InputSchema):
    title: NonEmptyText | None = None
    cover_url: AnyHttpUrl | None = None
    release_date: date | None = None
    artist_ids: list[PositiveId] | None = Field(
        default=None, min_length=1, max_length=MAX_RELATIONS
    )
    genre_ids: list[PositiveId] | None = Field(default=None, max_length=MAX_RELATIONS)

    @field_validator("title", "artist_ids", "genre_ids")
    @classmethod
    def reject_null_or_duplicates(cls, value: object) -> object:
        if value is None:
            raise ValueError("field cannot be null; omit it to keep the current value")
        if isinstance(value, list) and len(set(value)) != len(value):
            raise ValueError("IDs must be unique")
        return value
