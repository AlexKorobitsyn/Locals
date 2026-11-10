"""Внешние идентификаторы городов GeoNames.

Revision ID: 0007_geonames_cities
Revises: 0006_community_xp
"""

import sqlalchemy as sa

from alembic import op

revision = "0007_geonames_cities"
down_revision = "0006_community_xp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cities", sa.Column("geoname_id", sa.Integer(), nullable=True))
    op.create_unique_constraint(op.f("uq_cities_geoname_id"), "cities", ["geoname_id"])
    op.create_check_constraint(
        op.f("ck_cities_geoname_id_positive"), "cities", "geoname_id > 0"
    )
    # Разные населённые пункты одного региона могут иметь одинаковые названия.
    op.drop_constraint(op.f("uq_cities_name"), "cities", type_="unique")
    op.create_index(
        "uq_cities_manual_identity",
        "cities",
        ["name", "region", "country"],
        unique=True,
        postgresql_nulls_not_distinct=True,
        postgresql_where=sa.text("geoname_id IS NULL"),
    )


def downgrade() -> None:
    duplicates = op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM cities GROUP BY name, region, country "
            "HAVING count(*) > 1)"
        )
    )
    if duplicates:
        raise RuntimeError(
            "Cannot restore the old city constraint: distinct places share names; "
            "resolve these records before downgrading"
        )
    op.drop_index("uq_cities_manual_identity", table_name="cities")
    op.create_unique_constraint(
        op.f("uq_cities_name"),
        "cities",
        ["name", "region", "country"],
        postgresql_nulls_not_distinct=True,
    )
    op.drop_constraint(op.f("ck_cities_geoname_id_positive"), "cities", type_="check")
    op.drop_constraint(op.f("uq_cities_geoname_id"), "cities", type_="unique")
    op.drop_column("cities", "geoname_id")
