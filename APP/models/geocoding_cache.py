from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from APP.core.constants import SHA256_LENGTH
from APP.models.base import Base


class GeocodingCache(Base):
    __tablename__ = "geocoding_cache"
    __table_args__ = (
        CheckConstraint("expires_at > requested_at", name="expiry_valid"),
    )

    cache_key: Mapped[str] = mapped_column(String(SHA256_LENGTH), primary_key=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    address: Mapped[str | None] = mapped_column(Text)
    failed: Mapped[bool]
