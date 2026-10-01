from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from APP.core.constants import RatingTarget
from APP.models.base import Base, TimestampMixin


class Rating(TimestampMixin, Base):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id"),
        Index("ix_ratings_target", "target_type", "target_id"),
        CheckConstraint("target_id > 0", name="target_id_positive"),
        CheckConstraint(
            "value BETWEEN 1 AND 5 AND mod(value, 0.5) = 0", name="value_valid"
        ),
        CheckConstraint(
            "weight > 0 AND weight < 'Infinity'::numeric", name="weight_valid"
        ),
        CheckConstraint(
            "num_nonnulls(track_id, album_id, artist_id, venue_id) = 1 AND ("
            "(target_type = 'track' AND track_id IS NOT NULL AND target_id = track_id) OR "
            "(target_type = 'album' AND album_id IS NOT NULL AND target_id = album_id) OR "
            "(target_type = 'artist' AND artist_id IS NOT NULL AND target_id = artist_id) OR "
            "(target_type = 'venue' AND venue_id IS NOT NULL AND target_id = venue_id))",
            name="target_consistent",
        ),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    # Удаление аккаунта требует сначала снять оценки и обновить агрегаты.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    target_type: Mapped[RatingTarget] = mapped_column(
        Enum(
            RatingTarget,
            name="rating_target",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        )
    )
    target_id: Mapped[int] = mapped_column(Integer)
    track_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), index=True
    )
    album_id: Mapped[int | None] = mapped_column(
        ForeignKey("albums.id", ondelete="CASCADE"), index=True
    )
    artist_id: Mapped[int | None] = mapped_column(
        ForeignKey("artists.id", ondelete="CASCADE"), index=True
    )
    venue_id: Mapped[int | None] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"), index=True
    )
    value: Mapped[Decimal] = mapped_column(Numeric())
    weight: Mapped[Decimal] = mapped_column(Numeric(20, 6))
