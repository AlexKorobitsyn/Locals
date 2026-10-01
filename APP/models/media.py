from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from APP.core.constants import NAME_MAX_LENGTH, ROLE_MAX_LENGTH, SHA256_LENGTH
from APP.models.base import Base, TimestampMixin


class Media(TimestampMixin, Base):
    __tablename__ = "media"
    __table_args__ = (
        CheckConstraint("status IN ('pending','ready')", name="status_valid"),
        CheckConstraint("kind IN ('audio','image')", name="kind_valid"),
        CheckConstraint("size > 0", name="size_positive"),
        CheckConstraint(
            "(kind = 'audio' AND duration IS NOT NULL AND duration > 0 AND width IS NULL AND height IS NULL) OR (kind = 'image' AND width IS NOT NULL AND height IS NOT NULL AND width > 0 AND height > 0 AND duration IS NULL)",
            name="metadata_valid",
        ),
    )
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(ROLE_MAX_LENGTH), server_default="pending"
    )
    kind: Mapped[str] = mapped_column(String(ROLE_MAX_LENGTH))
    object_key: Mapped[str] = mapped_column(Text, unique=True)
    filename: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    content_type: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(SHA256_LENGTH))
    duration: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
