from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Identity,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from APP.core.constants import NAME_MAX_LENGTH
from APP.models.base import Base, RatedMixin, TimestampMixin

if TYPE_CHECKING:
    from APP.models.artist import Artist
    from APP.models.genre import Genre
    from APP.models.track import Track

album_artists = Table(
    "album_artists",
    Base.metadata,
    Column("album_id", ForeignKey("albums.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "artist_id",
        ForeignKey("artists.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)


class Album(RatedMixin, TimestampMixin, Base):
    __tablename__ = "albums"
    __table_args__ = (
        *RatedMixin.rating_constraints(),
        CheckConstraint("length(btrim(title)) > 0", name="title_nonempty"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    title: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), index=True)
    cover_url: Mapped[str | None] = mapped_column(Text)
    image_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("media.id", ondelete="RESTRICT"), index=True
    )
    release_date: Mapped[date | None] = mapped_column(Date)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    artists: Mapped[list[Artist]] = relationship(
        secondary=album_artists, back_populates="albums", lazy="raise"
    )
    genres: Mapped[list[Genre]] = relationship(secondary="album_genres", lazy="raise")
    tracks: Mapped[list[Track]] = relationship(
        back_populates="album", passive_deletes=True, lazy="raise"
    )
