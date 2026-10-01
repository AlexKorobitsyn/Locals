from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from APP.core.constants import DEFAULT_MEMBER_ROLE, ROLE_MAX_LENGTH
from APP.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from APP.models.artist import Artist
    from APP.models.user import User


class ArtistMember(TimestampMixin, Base):
    __tablename__ = "artist_members"
    __table_args__ = (CheckConstraint("length(btrim(role)) > 0", name="role_nonempty"),)

    artist_id: Mapped[int] = mapped_column(
        ForeignKey("artists.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    role: Mapped[str] = mapped_column(
        String(ROLE_MAX_LENGTH),
        primary_key=True,
        default=DEFAULT_MEMBER_ROLE,
        server_default=DEFAULT_MEMBER_ROLE,
    )

    artist: Mapped[Artist] = relationship(back_populates="memberships", lazy="raise")
    user: Mapped[User] = relationship(lazy="raise")
