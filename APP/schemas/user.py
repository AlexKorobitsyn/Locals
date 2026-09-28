# APP/schemas/user.py

from pydantic import BaseModel
from datetime import datetime
from city import CityOut

class UserShort(BaseModel):
    id: int
    display_name: str
    avatar_url: str | None

class UserOut(UserShort):
    bio: str | None = None
    type: str
    city: CityOut | None = None

class UserMe(UserOut):
    email: str
    level: str
    created_at: datetime