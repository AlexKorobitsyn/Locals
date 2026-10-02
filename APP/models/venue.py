from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from APP.core.constants import NAME_MAX_LENGTH
from APP.models.base import Base, RatedMixin, TimestampMixin

if TYPE_CHECKING:
    from APP.models.city import City


class Venue(RatedMixin, TimestampMixin, Base):
    __tablename__ = "venues"
    __table_args__ = (
        CheckConstraint(
            "publication_status IN ('pending','published','rejected')",
            name="publication_status_valid",
        ),
        *RatedMixin.rating_constraints(),
        CheckConstraint("length(btrim(name)) > 0", name="name_nonempty"),
        CheckConstraint("lat BETWEEN -90 AND 90", name="latitude_valid"),
        CheckConstraint("lng BETWEEN -180 AND 180", name="longitude_valid"),
        CheckConstraint(
            "capacity IS NULL OR capacity >= 0", name="capacity_nonnegative"
        ),
    )

    publication_status: Mapped[str] = mapped_column(
        String(64), server_default="published", index=True
    )
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(Text)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    image_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("media.id", ondelete="RESTRICT"), index=True
    )

    city_id: Mapped[int] = mapped_column(
        ForeignKey("cities.id", ondelete="RESTRICT"), index=True
    )
    address: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)

    capacity: Mapped[int | None] = mapped_column(Integer)
    website: Mapped[str | None] = mapped_column(Text)

    city: Mapped[City] = relationship(lazy="raise")
