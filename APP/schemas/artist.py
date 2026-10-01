from pydantic import AnyHttpUrl, Field, field_validator

from APP.core.constants import BIO_MAX_LENGTH, MAX_RELATIONS
from APP.schemas.city import CityOut
from APP.schemas.common import (
    BaseSchema,
    InputSchema,
    NonEmptyText,
    NonNegativeInt,
    PositiveId,
    RatingFields,
)
from APP.schemas.genre import GenreOut


class ArtistShort(BaseSchema):
    id: int
    name: str
    image_url: str | None = None


class ArtistRatedShort(ArtistShort, RatingFields):
    pass


class ArtistOut(ArtistRatedShort):
    bio: str | None = None
    city: CityOut | None = None
    genres: list[GenreOut] = Field(default_factory=list)
    albums_count: NonNegativeInt = 0
    tracks_count: NonNegativeInt = 0
    followers_count: NonNegativeInt = 0
    user_id: int | None = None
    is_owner: bool = False
    is_followed_by_me: bool = False


class ArtistCreate(InputSchema):
    name: NonEmptyText
    bio: str | None = Field(default=None, max_length=BIO_MAX_LENGTH)
    image_url: AnyHttpUrl | None = None
    city_id: PositiveId | None = None
    genre_ids: list[PositiveId] = Field(default_factory=list, max_length=MAX_RELATIONS)

    @field_validator("genre_ids")
    @classmethod
    def unique_genres(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("genre_ids must be unique")
        return value


class ArtistUpdate(InputSchema):
    name: NonEmptyText | None = None
    bio: str | None = Field(default=None, max_length=BIO_MAX_LENGTH)
    image_url: AnyHttpUrl | None = None
    city_id: PositiveId | None = None
    genre_ids: list[PositiveId] | None = Field(default=None, max_length=MAX_RELATIONS)

    @field_validator("name", "genre_ids")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field cannot be null; omit it to keep the current value")
        if isinstance(value, list) and len(set(value)) != len(value):
            raise ValueError("genre_ids must be unique")
        return value
