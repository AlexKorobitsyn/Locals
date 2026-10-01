# APP/schemas/venue.py

from city import CityShort
from common import BaseSchema

class VenueShort(BaseSchema):
    id: int
    name: str
    cover_url: str | None
    city: CityShort


class VenueRatedShort(VenueShort):
    rating_avg: float | None = None
    ratings_count: int = 0
    my_rating: int | None = None


class VenueOut(VenueRatedShort):
    description: str | None = None
    address: str | None = None
    lat: float
    lng: float
    capacity: int | None = None
    website: str | None = None
    events_count: int = 0
    followers_count: int = 0