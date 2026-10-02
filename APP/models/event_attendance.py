from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from APP.models.base import Base, TimestampMixin


class EventAttendance(TimestampMixin, Base):
    __tablename__ = "event_attendance"
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
