from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Identity, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from APP.core.constants import NAME_MAX_LENGTH
from APP.models.base import Base, RatedMixin, TimestampMixin

if TYPE_CHECKING:
    from APP.models.album import Album
    from APP.models.artist_member import ArtistMember
    from APP.models.city import City
    from APP.models.genre import Genre
    from APP.models.track_artist import TrackArtist
    from APP.models.user import User


class Artist(RatedMixin, TimestampMixin, Base):
    __tablename__ = "artists"
    __table_args__ = (
        *RatedMixin.rating_constraints(),
        CheckConstraint("length(btrim(name)) > 0", name="name_nonempty"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), index=True)
    bio: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    image_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("media.id", ondelete="RESTRICT"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    city_id: Mapped[int | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"), index=True
    )

    owner: Mapped[User | None] = relationship(back_populates="artists", lazy="raise")
    city: Mapped[City | None] = relationship(lazy="raise")
    genres: Mapped[list[Genre]] = relationship(secondary="artist_genres", lazy="raise")
    albums: Mapped[list[Album]] = relationship(
        secondary="album_artists", back_populates="artists", lazy="raise"
    )
    memberships: Mapped[list[ArtistMember]] = relationship(
        back_populates="artist",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )
    members: Mapped[list[User]] = relationship(
        secondary="artist_members", viewonly=True, lazy="raise"
    )
    track_credits: Mapped[list[TrackArtist]] = relationship(
        back_populates="artist",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )
