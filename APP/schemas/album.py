# APP/schemas/album.py
from pydantic import BaseModel
from datetime import date
from artist import ArtistShort

class AlbumShort(BaseModel):
    id: int
    title: str
    cover_url: str | None
    release_date: date | None
    artists: list[ArtistShort] = []


class AlbumRatedShort(AlbumShort):
    rating_avg: float | None = None
    ratings_count: int = 0
    my_rating: int | None = None


class AlbumOut(AlbumRatedShort):
    genres: list[str] = []
    tracks_count: int = 0
    duration: int = 0
