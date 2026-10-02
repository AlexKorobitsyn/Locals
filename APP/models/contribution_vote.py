from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from APP.models.base import Base, TimestampMixin


class ContributionVote(TimestampMixin, Base):
    __tablename__ = "contribution_votes"
    contribution_id: Mapped[int] = mapped_column(
        ForeignKey("contributions.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
