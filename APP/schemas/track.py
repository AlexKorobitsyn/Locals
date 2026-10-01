# APP/schemas/track.py
from common import BaseSchema
from datetime import datetime
from album import AlbumShort
from genre import GenreOut
from artist import ArtistShort

class TrackShort(BaseSchema):
    id: int
    title: str
    duration: int
    cover_url: str | None
    rating_avg: float | None = None
    ratings_count: int = 0
    my_rating: int | None = None

class TrackOut(TrackShort):
    album: AlbumShort | None = None
    artists: list[ArtistShort] = []
    genres: list[GenreOut] = []
    lyrics: str | None = None
    created_at: datetime

class TrackCreate(BaseSchema): # то что клиент присылает при создании
    title: str
    album_id: int | None = None
    artist_ids: list[int] = []
    duration: int

class TrackUpdate(BaseSchema): # что можно редактировать
    title: str | None = None
    album_id: int | None = None
    artist_ids: list[int] | None = None