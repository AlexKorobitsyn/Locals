from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Identity,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from APP.models.base import Base, TimestampMixin


class ExperienceAward(TimestampMixin, Base):
    __tablename__ = "experience_awards"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "source_key", name="uq_experience_awards_user_source"
        ),
        CheckConstraint("points > 0", name="points_positive"),
    )
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    track_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracks.id", ondelete="SET NULL")
    )
    source_key: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(64))
    day: Mapped[date] = mapped_column(Date, index=True)
    points: Mapped[int] = mapped_column(Integer)
