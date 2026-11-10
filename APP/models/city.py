from sqlalchemy import CheckConstraint, Float, Identity, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from APP.core.constants import NAME_MAX_LENGTH, ROLE_MAX_LENGTH
from APP.models.base import Base, TimestampMixin


class City(TimestampMixin, Base):
    __tablename__ = "cities"
    __table_args__ = (
        Index(
            "uq_cities_manual_identity",
            "name",
            "region",
            "country",
            unique=True,
            postgresql_nulls_not_distinct=True,
            postgresql_where=text("geoname_id IS NULL"),
        ),
        CheckConstraint("geoname_id > 0", name="geoname_id_positive"),
        CheckConstraint("length(btrim(name)) > 0", name="name_nonempty"),
        CheckConstraint("length(btrim(country)) > 0", name="country_nonempty"),
        CheckConstraint("lat BETWEEN -90 AND 90", name="latitude_valid"),
        CheckConstraint("lng BETWEEN -180 AND 180", name="longitude_valid"),
        CheckConstraint("length(btrim(timezone)) > 0", name="timezone_nonempty"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    geoname_id: Mapped[int | None] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), index=True)
    region: Mapped[str | None] = mapped_column(String(NAME_MAX_LENGTH))
    country: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    timezone: Mapped[str] = mapped_column(String(ROLE_MAX_LENGTH))
