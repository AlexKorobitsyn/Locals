# APP/schemas/user.py

from common import BaseSchema
from datetime import datetime
from city import CityOut

class UserShort(BaseSchema):
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