"""Общий кэш и ограничение частоты геокодирования.

Revision ID: 0008_geocoding_cache
Revises: 0007_geonames_cities
"""

import sqlalchemy as sa

from alembic import op

revision = "0008_geocoding_cache"
down_revision = "0007_geonames_cities"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "geocoding_cache",
        sa.Column("cache_key", sa.String(64), primary_key=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("failed", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "expires_at > requested_at", name=op.f("ck_geocoding_cache_expiry_valid")
        ),
    )
    op.create_index(
        "ix_geocoding_cache_requested_at", "geocoding_cache", ["requested_at"]
    )


def downgrade():
    op.drop_table("geocoding_cache")
