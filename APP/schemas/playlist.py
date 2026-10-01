from datetime import datetime
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator

from APP.core.constants import DESCRIPTION_MAX_LENGTH, PLAYLIST_MAX_TRACKS, PlaylistKind
from APP.schemas.common import (
    BaseSchema,
    InputSchema,
    NonEmptyText,
    NonNegativeInt,
    PositiveId,
)
from APP.schemas.track import TrackRatedShort
from APP.schemas.user import UserShort


class PlaylistShort(BaseSchema):
    id: int
    name: str
    cover_url: str | None = None
    tracks_count: NonNegativeInt = 0
    likes_count: NonNegativeInt = 0
    kind: PlaylistKind = PlaylistKind.custom
    visibility: Literal["public", "private"] = "private"
    is_owner: bool = False
    is_liked_by_me: bool = False


class PlaylistTrackItem(BaseSchema):
    track: TrackRatedShort
    position: NonNegativeInt
    added_at: datetime


class PlaylistOut(PlaylistShort):
    description: str | None = None
    owner: UserShort
    visibility: Literal["public", "private"]
    is_owner: bool = False
    is_liked_by_me: bool = False
    created_at: datetime
    updated_at: datetime
    kind: PlaylistKind = PlaylistKind.custom


class PlaylistCreate(InputSchema):
    name: NonEmptyText
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    visibility: Literal["public", "private"] = "private"
    cover_url: AnyHttpUrl | None = None


class PlaylistUpdate(InputSchema):
    name: NonEmptyText | None = None
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    visibility: Literal["public", "private"] | None = None
    cover_url: AnyHttpUrl | None = None

    @field_validator("name", "visibility")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("field cannot be null")
        return value


class PlaylistTrackAdd(InputSchema):
    track_id: PositiveId
    position: int | None = Field(default=None, ge=0, le=PLAYLIST_MAX_TRACKS)


class PlaylistReorder(InputSchema):
    track_ids: list[PositiveId] = Field(max_length=PLAYLIST_MAX_TRACKS)

    @field_validator("track_ids")
    @classmethod
    def unique_ids(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("track_ids must be unique")
        return value
