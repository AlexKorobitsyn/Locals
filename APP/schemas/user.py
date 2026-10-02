from datetime import datetime
from typing import Literal

from APP.schemas.city import CityOut
from APP.schemas.common import BaseSchema, NonNegativeInt


class UserShort(BaseSchema):
    id: int
    display_name: str
    avatar_url: str | None = None


class UserOut(UserShort):
    scene_verified: bool = False
    experience_points: NonNegativeInt = 0
    experience_level: int = 1
    level_name: str = "Новичок"
    bio: str | None = None
    type: Literal["user", "artist"]
    city: CityOut | None = None
    followers_count: NonNegativeInt = 0
    following_count: NonNegativeInt = 0
    is_followed_by_me: bool = False


class UserMe(UserOut):
    email: str
    level: Literal["green", "experienced", "moderator", "admin"]
    created_at: datetime
