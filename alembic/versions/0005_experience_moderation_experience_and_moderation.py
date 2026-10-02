"""experience and moderation

Revision ID: 0005_experience_moderation
Revises: 0004_library_media
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0005_experience_moderation"
down_revision = "0004_library_media"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contributions",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), nullable=True),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=True),
        sa.Column("album_id", sa.Integer(), nullable=True),
        sa.Column("artist_id", sa.Integer(), nullable=True),
        sa.Column("field", sa.String(length=64), nullable=False),
        sa.Column(
            "status", sa.String(length=64), server_default="pending", nullable=False
        ),
        sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("proposed", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reason", sa.String(length=10000), nullable=True),
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
            "field IN ('lyrics','genres') AND (field != 'lyrics' OR target_type = 'track')",
            name=op.f("ck_contributions_field_valid"),
        ),
        sa.CheckConstraint(
            "num_nonnulls(track_id, album_id, artist_id) = 1 AND ((target_type = 'track' AND track_id IS NOT NULL AND target_id = track_id) OR (target_type = 'album' AND album_id IS NOT NULL AND target_id = album_id) OR (target_type = 'artist' AND artist_id IS NOT NULL AND target_id = artist_id))",
            name=op.f("ck_contributions_target_consistent"),
        ),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected')",
            name=op.f("ck_contributions_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["album_id"],
            ["albums.id"],
            name=op.f("fk_contributions_album_id_albums"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["artist_id"],
            ["artists.id"],
            name=op.f("fk_contributions_artist_id_artists"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["users.id"],
            name=op.f("fk_contributions_reviewer_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_contributions_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_contributions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contributions")),
    )
    op.create_index(
        op.f("ix_contributions_status"), "contributions", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_contributions_user_id"), "contributions", ["user_id"], unique=False
    )
    op.create_table(
        "experience_awards",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=True),
        sa.Column("source_key", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
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
            "points > 0", name=op.f("ck_experience_awards_points_positive")
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_experience_awards_track_id_tracks"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_experience_awards_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experience_awards")),
        sa.UniqueConstraint(
            "user_id", "source_key", name="uq_experience_awards_user_source"
        ),
    )
    op.create_index(
        op.f("ix_experience_awards_day"), "experience_awards", ["day"], unique=False
    )
    op.create_index(
        op.f("ix_experience_awards_user_id"),
        "experience_awards",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "listening_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_playing", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "seconds",
            sa.Numeric(precision=20, scale=6),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "required_seconds", sa.Numeric(precision=20, scale=6), nullable=False
        ),
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
            "seconds >= 0 AND required_seconds > 0",
            name=op.f("ck_listening_sessions_seconds_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_listening_sessions_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_listening_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_listening_sessions")),
    )
    op.create_index(
        op.f("ix_listening_sessions_track_id"),
        "listening_sessions",
        ["track_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_listening_sessions_user_id"),
        "listening_sessions",
        ["user_id"],
        unique=False,
    )
    op.add_column(
        "users",
        sa.Column(
            "experience_points", sa.Integer(), server_default="0", nullable=False
        ),
    )
    op.create_check_constraint(
        op.f("ck_users_experience_points_nonnegative"),
        "users",
        "experience_points >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_users_experience_points_nonnegative"), "users", type_="check"
    )
    op.drop_column("users", "experience_points")
    op.drop_index(
        op.f("ix_listening_sessions_user_id"), table_name="listening_sessions"
    )
    op.drop_index(
        op.f("ix_listening_sessions_track_id"), table_name="listening_sessions"
    )
    op.drop_table("listening_sessions")
    op.drop_index(op.f("ix_experience_awards_user_id"), table_name="experience_awards")
    op.drop_index(op.f("ix_experience_awards_day"), table_name="experience_awards")
    op.drop_table("experience_awards")
    op.drop_index(op.f("ix_contributions_user_id"), table_name="contributions")
    op.drop_index(op.f("ix_contributions_status"), table_name="contributions")
    op.drop_table("contributions")
