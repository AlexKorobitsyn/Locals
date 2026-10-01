from typing import Literal

from APP.schemas.common import BaseSchema


class HealthOut(BaseSchema):
    status: Literal["ok"] = "ok"


class ReadinessOut(BaseSchema):
    status: Literal["ok", "unavailable"]
    database: Literal["ok", "unavailable"]


class VersionOut(BaseSchema):
    release_id: str
