# APP/schemas/track.py
from pydantic import BaseModel
from datetime import datetime
from album import AlbumShort
from genre import GenreOut
from artist import ArtistShort

class TrackSmallInfo(BaseModel): #чисто для списков, микроинфа про трек с обложкой
    id : int
    title : str
    duration : int
    cover_url: str | None

class TrackRatedSmallInfo(TrackSmallInfo): #то же, но с оценкой для списков
    rating_avg: float | None = None
    ratings_count: int = 0
    my_rating: int | None = None

class TrackOut(TrackRatedSmallInfo): #подробная информация, про группу, текст, оценка, когда заходишь на отдельный трек
    album: AlbumShort | None = None
    artists: list[ArtistShort] = []
    genres: list[GenreOut] = []
    lyrics: str | None = None
    created_at: datetime

class TrackCreate(BaseModel): # то что клиент присылает при создании
    title: str
    album_id: int | None = None
    artist_ids: list[int] = []
    duration: int

class TrackUpdate(BaseModel): # что можно редактировать
    title: str | None = None
    album_id: int | None = None
    artist_ids: list[int] | None = None