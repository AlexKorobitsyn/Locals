from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from APP.models.base import Base


class ReviewRewardText(Base):
    __tablename__ = "review_reward_texts"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
