from datetime import datetime

from APP.schemas.common import BaseSchema
from APP.schemas.user import UserShort


class ActivityOut(BaseSchema):
    id: int
    actor: UserShort | None = None
    action: str
    target_type: str
    target_id: int
    payload: dict
    created_at: datetime
