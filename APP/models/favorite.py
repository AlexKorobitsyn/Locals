from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Identity,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from APP.core.constants import FavoriteTarget
from APP.models.base import Base, TimestampMixin, target_constraint


class Favorite(TimestampMixin, Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "entity_type", "entity_id"),
        Index("ix_favorites_target", "entity_type", "entity_id"),
        CheckConstraint("entity_id > 0", name="entity_id_positive"),
        CheckConstraint(
            target_constraint(
                "entity_type", "entity_id", tuple(kind.value for kind in FavoriteTarget)
            ),
            name="target_consistent",
        ),
    )
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    entity_type: Mapped[FavoriteTarget] = mapped_column(
        Enum(
            FavoriteTarget,
            name="favorite_target",
            native_enum=False,
            create_constraint=True,
        )
    )
    entity_id: Mapped[int] = mapped_column()
    track_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), index=True
    )
    album_id: Mapped[int | None] = mapped_column(
        ForeignKey("albums.id", ondelete="CASCADE"), index=True
    )
    artist_id: Mapped[int | None] = mapped_column(
        ForeignKey("artists.id", ondelete="CASCADE"), index=True
    )
    playlist_id: Mapped[int | None] = mapped_column(
        ForeignKey("playlists.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    venue_id: Mapped[int | None] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"), index=True
    )
    review_id: Mapped[int | None] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), index=True
    )
