from sqlalchemy import CheckConstraint, ForeignKey, Identity, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from APP.models.base import Base, TimestampMixin, target_constraint


class Contribution(TimestampMixin, Base):
    __tablename__ = "contributions"
    __table_args__ = (
        CheckConstraint(
            target_constraint(
                "target_type",
                "target_id",
                ("track", "album", "artist", "venue", "event"),
            ),
            name="target_consistent",
        ),
        CheckConstraint(
            "status IN ('pending','approved','rejected')", name="status_valid"
        ),
        CheckConstraint(
            "(field = 'lyrics' AND target_type = 'track') OR (field IN ('genres','metadata') AND target_type IN ('track','album','artist')) OR (field = 'publication' AND target_type IN ('venue','event'))",
            name="field_valid",
        ),
    )
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    target_type: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[int] = mapped_column()
    track_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE")
    )
    album_id: Mapped[int | None] = mapped_column(
        ForeignKey("albums.id", ondelete="CASCADE")
    )
    artist_id: Mapped[int | None] = mapped_column(
        ForeignKey("artists.id", ondelete="CASCADE")
    )
    venue_id: Mapped[int | None] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE")
    )
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE")
    )
    field: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(
        String(64), server_default="pending", index=True
    )
    before: Mapped[dict] = mapped_column(JSONB)
    proposed: Mapped[dict] = mapped_column(JSONB)
    reason: Mapped[str | None] = mapped_column(String(10000))
