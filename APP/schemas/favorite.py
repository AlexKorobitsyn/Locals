from datetime import datetime

from APP.core.constants import FavoriteTarget
from APP.schemas.common import BaseSchema, InputSchema, PositiveId

FavoriteEntityType = FavoriteTarget


class FavoriteCreate(InputSchema):
    entity_type: FavoriteEntityType
    entity_id: PositiveId


class FavoriteRead(BaseSchema):
    id: int
    user_id: int
    entity_type: FavoriteEntityType
    entity_id: int
    created_at: datetime
