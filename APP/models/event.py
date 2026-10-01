from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Index,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from APP.core.constants import NAME_MAX_LENGTH
from APP.models.base import Base, TimestampMixin
from APP.models.city import City
from APP.models.event_type import EventType
from APP.models.venue import Venue

event_event_types = Table(
    "event_event_types",
    Base.metadata,
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "event_type_id",
        ForeignKey("event_types.id", ondelete="RESTRICT"),
        primary_key=True,
        index=True,
    ),
)


class Event(TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("length(btrim(name)) > 0", name="name_nonempty"),
        CheckConstraint("stop_at IS NULL OR stop_at > starts_at", name="dates_valid"),
        CheckConstraint("lat BETWEEN -90 AND 90", name="latitude_valid"),
        CheckConstraint("lng BETWEEN -180 AND 180", name="longitude_valid"),
        Index("ix_events_city_starts_at", "city_id", "starts_at"),
        Index("ix_events_coordinates", "lat", "lng"),
    )
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"))
    venue_id: Mapped[int | None] = mapped_column(
        ForeignKey("venues.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    description: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    stop_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    city: Mapped[City] = relationship(lazy="raise")
    venue: Mapped[Venue | None] = relationship(lazy="raise")
    type_event: Mapped[list[EventType]] = relationship(
        secondary=event_event_types, lazy="raise"
    )
