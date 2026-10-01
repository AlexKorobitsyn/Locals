from datetime import datetime

from APP.core.constants import FollowTarget
from APP.schemas.common import BaseSchema, InputSchema, PositiveId


class FollowCreate(InputSchema):
    target_type: FollowTarget
    target_id: PositiveId


class FollowOut(BaseSchema):
    id: int
    follower_id: int
    target_type: FollowTarget
    target_id: int
    created_at: datetime
