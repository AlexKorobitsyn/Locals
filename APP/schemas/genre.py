# APP/schemas/genre.py

from common import BaseSchema

class GenreOut(BaseSchema):
    id: int
    slug: str
    name: str