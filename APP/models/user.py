from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    exists,
    func,
)
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from APP.core.constants import (
    EMAIL_MAX_LENGTH,
    NAME_MAX_LENGTH,
    ROLE_MAX_LENGTH,
    UserLevel,
)
from APP.models.artist import Artist
from APP.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from APP.models.city import City
    from APP.models.genre import Genre


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("experience_points >= 0", name="experience_points_nonnegative"),
        CheckConstraint(
            "length(btrim(display_name)) > 0", name="display_name_nonempty"
        ),
        CheckConstraint("length(btrim(email)) > 0", name="email_nonempty"),
        CheckConstraint("length(password_hash) > 0", name="password_hash_nonempty"),
        CheckConstraint(
            "weight > 0 AND weight < 'Infinity'::float8", name="weight_valid"
        ),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH))
    password_hash: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    display_name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    image_media_id: Mapped[int | None] = mapped_column(
        ForeignKey("media.id", ondelete="RESTRICT", use_alter=True), index=True
    )
    bio: Mapped[str | None] = mapped_column(Text)
    level: Mapped[UserLevel] = mapped_column(
        Enum(
            UserLevel,
            name="user_level",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            length=ROLE_MAX_LENGTH,
        ),
        default=UserLevel.green,
        server_default=UserLevel.green.value,
    )
    weight: Mapped[Decimal] = mapped_column(Numeric(20, 6), server_default="1")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    scene_verified: Mapped[bool] = mapped_column(Boolean, server_default="false")
    experience_points: Mapped[int] = mapped_column(Integer, server_default="0")
    city_id: Mapped[int | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"), index=True
    )
    is_artist: Mapped[bool] = column_property(exists().where(Artist.user_id == id))

    city: Mapped[City | None] = relationship(lazy="raise")
    artists: Mapped[list[Artist]] = relationship(back_populates="owner", lazy="raise")
    favorite_genres: Mapped[list[Genre]] = relationship(
        secondary="user_favorite_genres", lazy="raise"
    )

    @property
    def type(self) -> str:
        # Творческая роль определяется владением Artist; права хранятся в level.
        return "artist" if self.is_artist else "user"


Index("uq_users_email_lower", func.lower(User.email), unique=True)
