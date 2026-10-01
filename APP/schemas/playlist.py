# APP/schemas/playlist.py
from track import TrackShort
from common import BaseSchema
from user import UserShort
from datetime import datetime

class PlaylistShort(BaseSchema):     # для списков плейлистов
    id: int
    name: str
    cover_url: str | None
    tracks_count: int = 0
    likes_count: int = 0


class PlaylistTrackItem(BaseSchema): # трек внутри плейлиста — с позицией
    track: TrackShort
    position: int
    added_at: datetime


class PlaylistOut(PlaylistShort):   # детальная страница плейлиста
    description: str | None = None
    owner: UserShort
    visibility: str                  # public | private
    is_owner: bool = False           # я владелец? (для кнопки «редактировать»)
    is_liked_by_me: bool = False     # я лайкнул?
    tracks: list[PlaylistTrackItem] = []
    created_at: datetime
    updated_at: datetime