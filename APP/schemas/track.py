from datetime import datetime
from typing import Annotated

from pydantic import (
    AnyHttpUrl,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from APP.core.constants import (
    DEFAULT_ARTIST_ROLE,
    LYRICS_MAX_LENGTH,
    MAX_DATABASE_INTEGER,
    MAX_RELATIONS,
    ROLE_MAX_LENGTH,
)
from APP.schemas.album import AlbumShort
from APP.schemas.artist import ArtistShort
from APP.schemas.common import (
    BaseSchema,
    InputSchema,
    NonEmptyText,
    NonNegativeInt,
    PositiveId,
    PositiveInteger,
    RatingFields,
)
from APP.schemas.genre import GenreOut


class TrackShort(BaseSchema):
    id: int
    title: str
    duration: NonNegativeInt
    cover_url: str | None = None


class TrackRatedShort(TrackShort, RatingFields):
    pass


class TrackOut(TrackRatedShort):
    album: AlbumShort | None = None
    artists: list[ArtistShort] = Field(default_factory=list)
    genres: list[GenreOut] = Field(default_factory=list)
    lyrics: str | None = None
    created_at: datetime
    artist_credits: list["TrackArtistOut"] = Field(default_factory=list)
    user_id: int | None = None
    is_owner: bool = False
    audio_media_id: int | None = None


class TrackArtistInput(InputSchema):
    artist_id: PositiveId
    role: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=1, max_length=ROLE_MAX_LENGTH
        ),
    ] = DEFAULT_ARTIST_ROLE


class TrackArtistOut(BaseSchema):
    artist: ArtistShort
    role: str


class TrackCreate(InputSchema):
    title: NonEmptyText
    album_id: PositiveId | None = None
    artist_ids: list[PositiveId] = Field(default_factory=list, max_length=MAX_RELATIONS)
    artist_credits: list[TrackArtistInput] = Field(
        default_factory=list, max_length=MAX_RELATIONS
    )
    duration: PositiveInteger = Field(le=MAX_DATABASE_INTEGER)
    cover_url: AnyHttpUrl | None = None
    lyrics: str | None = Field(default=None, max_length=LYRICS_MAX_LENGTH)
    genre_ids: list[PositiveId] = Field(default_factory=list, max_length=MAX_RELATIONS)

    @model_validator(mode="after")
    def validate_relations(self):
        validate_track_relations(self.artist_ids, self.artist_credits, self.genre_ids)
        return self


class TrackUpdate(InputSchema):
    title: NonEmptyText | None = None
    album_id: PositiveId | None = None
    artist_ids: list[PositiveId] | None = Field(default=None, max_length=MAX_RELATIONS)
    artist_credits: list[TrackArtistInput] | None = Field(
        default=None, max_length=MAX_RELATIONS
    )
    duration: PositiveInteger | None = Field(default=None, le=MAX_DATABASE_INTEGER)
    cover_url: AnyHttpUrl | None = None
    lyrics: str | None = Field(default=None, max_length=LYRICS_MAX_LENGTH)
    genre_ids: list[PositiveId] | None = Field(default=None, max_length=MAX_RELATIONS)

    @field_validator("title", "artist_ids", "artist_credits", "duration", "genre_ids")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field cannot be null; omit it to keep the current value")
        return value

    @model_validator(mode="after")
    def validate_relations(self):
        if {"artist_ids", "artist_credits"} <= self.model_fields_set:
            raise ValueError("use either artist_ids or artist_credits")
        validate_track_relations(
            self.artist_ids or [], self.artist_credits or [], self.genre_ids or []
        )
        return self


def validate_track_relations(
    ids: list[int], credits: list[TrackArtistInput], genres: list[int]
) -> None:
    if ids and credits:
        raise ValueError("use either artist_ids or artist_credits")
    keys = [(credit.artist_id, credit.role) for credit in credits]
    if (
        len(set(ids)) != len(ids)
        or len(set(keys)) != len(keys)
        or len(set(genres)) != len(genres)
    ):
        raise ValueError("relations must be unique")
