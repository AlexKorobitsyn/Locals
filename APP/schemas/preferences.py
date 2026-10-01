from pydantic import Field, field_validator

from APP.core.constants import MAX_RELATIONS
from APP.schemas.common import InputSchema, PositiveId


class FavoriteGenresPut(InputSchema):
    genre_ids: list[PositiveId] = Field(max_length=MAX_RELATIONS)

    @field_validator("genre_ids")
    @classmethod
    def unique_genres(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("genre_ids must be unique")
        return value
