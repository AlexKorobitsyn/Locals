from pydantic import Field

from APP.core.constants import DESCRIPTION_MAX_LENGTH
from APP.schemas.common import BaseSchema


class ReverseAddress(BaseSchema):
    address: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
