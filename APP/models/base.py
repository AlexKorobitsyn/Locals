from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Integer, MetaData, Numeric, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def target_constraint(
    discriminator: str, target_id: str, kinds: tuple[str, ...]
) -> str:
    columns = ", ".join(f"{kind}_id" for kind in kinds)
    matches = " OR ".join(
        f"({discriminator} = '{kind}' AND {kind}_id IS NOT NULL AND {target_id} = {kind}_id)"
        for kind in kinds
    )
    return f"num_nonnulls({columns}) = 1 AND ({matches})"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RatedMixin:
    rating_sum: Mapped[Decimal] = mapped_column(Numeric(30, 10), server_default="0")
    rating_weight: Mapped[Decimal] = mapped_column(Numeric(30, 10), server_default="0")
    ratings_count: Mapped[int] = mapped_column(Integer, server_default="0")

    @staticmethod
    def rating_constraints() -> tuple[CheckConstraint, ...]:
        return (
            CheckConstraint("ratings_count >= 0", name="ratings_count_nonnegative"),
            CheckConstraint(
                "rating_weight >= 0 AND rating_weight < 'Infinity'::float8",
                name="rating_weight_valid",
            ),
            CheckConstraint(
                "rating_sum >= rating_weight AND rating_sum <= 5 * rating_weight",
                name="rating_sum_valid",
            ),
            CheckConstraint(
                "(ratings_count = 0 AND rating_weight = 0 AND rating_sum = 0) "
                "OR (ratings_count > 0 AND rating_weight > 0)",
                name="rating_aggregates_consistent",
            ),
        )
