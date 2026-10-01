from typing import Annotated, Generic, TypeVar

from fastapi import Path, Query
from pydantic import BaseModel, Field

from APP.core.constants import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT

Item = TypeVar("Item")
PageLimit = Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)]
PageOffset = Annotated[int, Query(ge=0)]
EntityId = Annotated[int, Path(gt=0)]


class Page(BaseModel, Generic[Item]):
    items: list[Item]
    total: int = Field(ge=0)
    limit: int = DEFAULT_PAGE_LIMIT
    offset: int = 0
