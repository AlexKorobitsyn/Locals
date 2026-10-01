from sqlalchemy import CheckConstraint, Column, ForeignKey, Identity, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from APP.core.constants import NAME_MAX_LENGTH, SLUG_MAX_LENGTH
from APP.models.base import Base

user_favorite_genres = Table(
    "user_favorite_genres",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "genre_id",
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)
artist_genres = Table(
    "artist_genres",
    Base.metadata,
    Column("artist_id", ForeignKey("artists.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "genre_id",
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)
album_genres = Table(
    "album_genres",
    Base.metadata,
    Column("album_id", ForeignKey("albums.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "genre_id",
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)
track_genres = Table(
    "track_genres",
    Base.metadata,
    Column("track_id", ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "genre_id",
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)


class Genre(Base):
    __tablename__ = "genres"
    __table_args__ = (
        CheckConstraint("length(btrim(name)) > 0", name="name_nonempty"),
        CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="slug_valid"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    slug: Mapped[str] = mapped_column(String(SLUG_MAX_LENGTH), unique=True)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
