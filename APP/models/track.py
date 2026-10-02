from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Identity, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from APP.core.constants import NAME_MAX_LENGTH
from APP.models.base import Base, RatedMixin, TimestampMixin

if TYPE_CHECKING:
    from APP.models.album import Album
    from APP.models.artist import Artist
    from APP.models.genre import Genre
    from APP.models.track_artist import TrackArtist


class Track(RatedMixin, TimestampMixin, Base):
    __tablename__ = "tracks"
    __table_args__ = (
        *RatedMixin.rating_constraints(),
        CheckConstraint("length(btrim(title)) > 0", name="title_nonempty"),
        CheckConstraint("duration > 0", name="duration_positive"),
    )

    owner_fields: Mapped[list[str]] = mapped_column(JSONB, server_default="[]")
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    title: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), index=True)
    duration: Mapped[int] = mapped_column(Integer)
    cover_url: Mapped[str | None] = mapped_column(Text)
    lyrics: Mapped[str | None] = mapped_column(Text)
    audio_key: Mapped[str | None] = mapped_column(Text)
    audio_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("media.id", ondelete="RESTRICT"), index=True
    )
    image_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("media.id", ondelete="RESTRICT"), index=True
    )
    album_id: Mapped[int | None] = mapped_column(
        ForeignKey("albums.id", ondelete="SET NULL"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    album: Mapped[Album | None] = relationship(back_populates="tracks", lazy="raise")
    genres: Mapped[list[Genre]] = relationship(secondary="track_genres", lazy="raise")
    artist_credits: Mapped[list[TrackArtist]] = relationship(
        back_populates="track",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )
    artists: Mapped[list[Artist]] = relationship(
        secondary="track_artists", viewonly=True, lazy="raise"
    )
