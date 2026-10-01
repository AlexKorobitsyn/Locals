from typing import Annotated

from pydantic import StringConstraints

from APP.core.constants import SLUG_MAX_LENGTH
from APP.schemas.common import BaseSchema, InputSchema, NonEmptyText


class GenreOut(BaseSchema):
    id: int
    slug: str
    name: str


class GenreCreate(InputSchema):
    name: NonEmptyText
    slug: Annotated[
        str,
        StringConstraints(
            min_length=1,
            max_length=SLUG_MAX_LENGTH,
            pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
        ),
    ]
