# APP/schemas/review.py
from common import BaseSchema
from user import UserShort
from datetime import datetime

class ReviewShort(BaseSchema):        # для списков рецензий
    id: int
    title: str | None
    rating: float                      # 1..5
    likes_count: int = 0
    created_at: datetime


class ReviewOut(ReviewShort):        # детальная рецензия
    text: str
    author: UserShort
    target_type: str                 # "track" | "album" | "artist" | "venue"
    target_id: int
    is_liked_by_me: bool = False
    is_owner: bool = False
    updated_at: datetime