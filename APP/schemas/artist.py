# APP/schemas/artist.py
from pydantic import BaseModel
from city import CityOut
from genre import GenreOut
from user import UserShort

class ArtistShort(BaseModel):
    id: int
    name: str
    image_url: str | None


class ArtistRatedShort(ArtistShort):
    rating_avg: float | None = None
    ratings_count: int = 0
    my_rating: int | None = None


class ArtistOut(ArtistRatedShort):
    bio: str | None = None
    city: CityOut | None = None
    genres: list[GenreOut] = []
    albums_count: int = 0
    tracks_count: int = 0
    followers_count: int = 0
    user_id: int | None = None
    is_owner: bool = False
    is_followed_by_me: bool = False