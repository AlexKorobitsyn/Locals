from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Identity,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from APP.core.constants import NAME_MAX_LENGTH, PlaylistKind
from APP.models.base import Base, TimestampMixin
from APP.models.user import User


class Playlist(TimestampMixin, Base):
    __tablename__ = "playlists"
    __table_args__ = (
        CheckConstraint("length(btrim(name)) > 0", name="name_nonempty"),
        CheckConstraint(
            "kind <> 'liked' OR visibility = 'private'", name="liked_private"
        ),
        Index(
            "uq_playlists_liked_user",
            "user_id",
            unique=True,
            postgresql_where=text("kind = 'liked'"),
        ),
    )
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(Text)
    image_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("media.id", ondelete="RESTRICT"), index=True
    )
    visibility: Mapped[str] = mapped_column(
        Enum(
            "public",
            "private",
            name="playlist_visibility",
            native_enum=False,
            create_constraint=True,
        ),
        server_default="private",
    )
    kind: Mapped[PlaylistKind] = mapped_column(
        Enum(
            PlaylistKind,
            name="playlist_kind",
            native_enum=False,
            create_constraint=True,
        ),
        server_default="custom",
    )
    owner: Mapped[User] = relationship(lazy="raise")
