"""Оценки и точные агрегаты рейтинга

Revision ID: 0003_ratings
Revises: 0002_auth_events
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_ratings"
down_revision = "0002_auth_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "target_type",
            sa.Enum(
                "track",
                "album",
                "artist",
                "venue",
                name="rating_target",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=True),
        sa.Column("album_id", sa.Integer(), nullable=True),
        sa.Column("artist_id", sa.Integer(), nullable=True),
        sa.Column("venue_id", sa.Integer(), nullable=True),
        sa.Column("value", sa.Numeric(), nullable=False),
        sa.Column("weight", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "num_nonnulls(track_id, album_id, artist_id, venue_id) = 1 AND ((target_type = 'track' AND track_id IS NOT NULL AND target_id = track_id) OR (target_type = 'album' AND album_id IS NOT NULL AND target_id = album_id) OR (target_type = 'artist' AND artist_id IS NOT NULL AND target_id = artist_id) OR (target_type = 'venue' AND venue_id IS NOT NULL AND target_id = venue_id))",
            name=op.f("ck_ratings_target_consistent"),
        ),
        sa.CheckConstraint(
            "weight > 0 AND weight < 'Infinity'::numeric",
            name=op.f("ck_ratings_weight_valid"),
        ),
        sa.CheckConstraint("target_id > 0", name=op.f("ck_ratings_target_id_positive")),
        sa.CheckConstraint(
            "value BETWEEN 1 AND 5 AND mod(value, 0.5) = 0",
            name=op.f("ck_ratings_value_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["album_id"],
            ["albums.id"],
            name=op.f("fk_ratings_album_id_albums"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["artist_id"],
            ["artists.id"],
            name=op.f("fk_ratings_artist_id_artists"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_ratings_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_ratings_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["venue_id"],
            ["venues.id"],
            name=op.f("fk_ratings_venue_id_venues"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ratings")),
        sa.UniqueConstraint(
            "user_id", "target_type", "target_id", name=op.f("uq_ratings_user_id")
        ),
    )
    op.create_index(op.f("ix_ratings_album_id"), "ratings", ["album_id"], unique=False)
    op.create_index(
        op.f("ix_ratings_artist_id"), "ratings", ["artist_id"], unique=False
    )
    op.create_index(
        "ix_ratings_target", "ratings", ["target_type", "target_id"], unique=False
    )
    op.create_index(op.f("ix_ratings_track_id"), "ratings", ["track_id"], unique=False)
    op.create_index(op.f("ix_ratings_venue_id"), "ratings", ["venue_id"], unique=False)
    op.alter_column(
        "albums",
        "rating_sum",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=30, scale=10),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "albums",
        "rating_weight",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=30, scale=10),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "artists",
        "rating_sum",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=30, scale=10),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "artists",
        "rating_weight",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=30, scale=10),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "tracks",
        "rating_sum",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=30, scale=10),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "tracks",
        "rating_weight",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=30, scale=10),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "users",
        "weight",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=20, scale=6),
        existing_nullable=False,
        server_default=sa.text("1"),
    )
    op.alter_column(
        "venues",
        "rating_sum",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=30, scale=10),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "venues",
        "rating_weight",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=30, scale=10),
        existing_nullable=False,
        server_default=sa.text("0"),
    )


def downgrade() -> None:
    op.alter_column(
        "venues",
        "rating_weight",
        existing_type=sa.Numeric(precision=30, scale=10),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "venues",
        "rating_sum",
        existing_type=sa.Numeric(precision=30, scale=10),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "users",
        "weight",
        existing_type=sa.Numeric(precision=20, scale=6),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
        server_default=sa.text("1"),
    )
    op.alter_column(
        "tracks",
        "rating_weight",
        existing_type=sa.Numeric(precision=30, scale=10),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "tracks",
        "rating_sum",
        existing_type=sa.Numeric(precision=30, scale=10),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "artists",
        "rating_weight",
        existing_type=sa.Numeric(precision=30, scale=10),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "artists",
        "rating_sum",
        existing_type=sa.Numeric(precision=30, scale=10),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "albums",
        "rating_weight",
        existing_type=sa.Numeric(precision=30, scale=10),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.alter_column(
        "albums",
        "rating_sum",
        existing_type=sa.Numeric(precision=30, scale=10),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
        server_default=sa.text("0"),
    )
    op.drop_index(op.f("ix_ratings_venue_id"), table_name="ratings")
    op.drop_index(op.f("ix_ratings_track_id"), table_name="ratings")
    op.drop_index("ix_ratings_target", table_name="ratings")
    op.drop_index(op.f("ix_ratings_artist_id"), table_name="ratings")
    op.drop_index(op.f("ix_ratings_album_id"), table_name="ratings")
    op.drop_table("ratings")
