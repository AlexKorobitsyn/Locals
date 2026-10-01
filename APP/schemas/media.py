from datetime import datetime
from typing import Literal

from APP.schemas.common import BaseSchema, InputSchema, PositiveId


class MediaOut(BaseSchema):
    id: int
    kind: Literal["audio", "image"]
    filename: str
    content_type: str
    size: int
    sha256: str
    duration: float | None = None
    width: int | None = None
    height: int | None = None
    created_at: datetime


class MediaAttach(InputSchema):
    media_id: PositiveId


class PlaybackOut(BaseSchema):
    url: str
    expires_in: int
    content_type: str
    duration: float
