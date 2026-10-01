from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from APP.core.constants import DEFAULT_ARTIST_ROLE, ROLE_MAX_LENGTH
from APP.models.base import Base

if TYPE_CHECKING:
    from APP.models.artist import Artist
    from APP.models.track import Track


class TrackArtist(Base):
    __tablename__ = "track_artists"
    __table_args__ = (CheckConstraint("length(btrim(role)) > 0", name="role_nonempty"),)

    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True
    )
    artist_id: Mapped[int] = mapped_column(
        ForeignKey("artists.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    role: Mapped[str] = mapped_column(
        String(ROLE_MAX_LENGTH),
        primary_key=True,
        default=DEFAULT_ARTIST_ROLE,
        server_default=DEFAULT_ARTIST_ROLE,
    )

    track: Mapped[Track] = relationship(back_populates="artist_credits", lazy="raise")
    artist: Mapped[Artist] = relationship(back_populates="track_credits", lazy="raise")
