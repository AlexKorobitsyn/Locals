# APP/schemas/genre.py

from pydantic import BaseModel

class GenreOut(BaseModel):
    id: int
    slug: str
    name: str