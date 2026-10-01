from sqlalchemy import CheckConstraint, ForeignKey, Identity, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from APP.core.constants import NAME_MAX_LENGTH
from APP.models.base import Base, TimestampMixin
from APP.models.rating import Rating


class Review(TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (CheckConstraint("length(btrim(text)) > 0", name="text_nonempty"),)
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    rating_id: Mapped[int] = mapped_column(
        ForeignKey("ratings.id", ondelete="CASCADE"), unique=True
    )
    title: Mapped[str | None] = mapped_column(String(NAME_MAX_LENGTH))
    text: Mapped[str] = mapped_column(Text)
    rating: Mapped[Rating] = relationship(lazy="raise")
