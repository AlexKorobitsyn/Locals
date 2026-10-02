from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from APP.models.base import Base, TimestampMixin


class ListeningSession(TimestampMixin, Base):
    __tablename__ = "listening_sessions"
    __table_args__ = (
        CheckConstraint("seconds >= 0 AND required_seconds > 0", name="seconds_valid"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), index=True
    )
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_playing: Mapped[bool] = mapped_column(Boolean, server_default="true")
    seconds: Mapped[Decimal] = mapped_column(Numeric(20, 6), server_default="0")
    required_seconds: Mapped[Decimal] = mapped_column(Numeric(20, 6))
