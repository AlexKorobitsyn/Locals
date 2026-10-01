# APP/schemas/favorite.py
from common import BaseSchema
from datetime import datetime


class FavoriteEntityType(str, Enum):
    track = "track"
    album = "album"
    artist = "artist"
    playlist = "playlist"
    event = "event"
    venue = "venue"

class FavoriteCreate(BaseSchema):
    entity_type: FavoriteEntityType
    entity_id: int

class FavoriteRead(BaseSchema):
    id: int
    user_id: int
    entity_type: FavoriteEntityType
    entity_id: int
    created_at: datetime