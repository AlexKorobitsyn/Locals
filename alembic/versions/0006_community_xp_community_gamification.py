"""Опыт, голоса сообщества и публикация предложений

Revision ID: 0006_community_xp
Revises: 0005_experience_moderation
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0006_community_xp"
down_revision = "0005_experience_moderation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        op.f("ck_contributions_target_consistent"), "contributions", type_="check"
    )
    op.drop_constraint(
        op.f("ck_contributions_field_valid"), "contributions", type_="check"
    )
    op.create_table(
        "review_reward_texts",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_review_reward_texts_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_id", "digest", name=op.f("pk_review_reward_texts")
        ),
    )
    op.create_table(
        "event_attendance",
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_event_attendance_event_id_events"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_event_attendance_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "event_id", "user_id", name=op.f("pk_event_attendance")
        ),
    )
    op.create_table(
        "contribution_votes",
        sa.Column("contribution_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["contribution_id"],
            ["contributions.id"],
            name=op.f("fk_contribution_votes_contribution_id_contributions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_contribution_votes_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "contribution_id", "user_id", name=op.f("pk_contribution_votes")
        ),
    )
    op.add_column(
        "albums",
        sa.Column(
            "owner_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.add_column(
        "artists",
        sa.Column(
            "owner_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.add_column("contributions", sa.Column("venue_id", sa.Integer(), nullable=True))
    op.add_column("contributions", sa.Column("event_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_contributions_event_id_events"),
        "contributions",
        "events",
        ["event_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_contributions_venue_id_venues"),
        "contributions",
        "venues",
        ["venue_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.add_column(
        "events",
        sa.Column(
            "publication_status",
            sa.String(length=64),
            server_default="published",
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_events_publication_status"),
        "events",
        ["publication_status"],
        unique=False,
    )
    op.add_column(
        "tracks",
        sa.Column(
            "owner_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "scene_verified", sa.Boolean(), server_default="false", nullable=False
        ),
    )
    op.add_column(
        "venues",
        sa.Column(
            "publication_status",
            sa.String(length=64),
            server_default="published",
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_venues_publication_status"),
        "venues",
        ["publication_status"],
        unique=False,
    )

    from APP.models.base import target_constraint

    op.create_check_constraint(
        "target_consistent",
        "contributions",
        target_constraint(
            "target_type", "target_id", ("track", "album", "artist", "venue", "event")
        ),
    )
    op.create_check_constraint(
        "field_valid",
        "contributions",
        "(field = 'lyrics' AND target_type = 'track') OR (field IN ('genres','metadata') AND target_type IN ('track','album','artist')) OR (field = 'publication' AND target_type IN ('venue','event'))",
    )
    for table in ("events", "venues"):
        op.create_check_constraint(
            "publication_status_valid",
            table,
            "publication_status IN ('pending','published','rejected')",
        )
    # Существующие тексты и жанры владельцев сохраняют приоритет после обновления.
    for table, kind in (
        ("artists", "artist"),
        ("albums", "album"),
        ("tracks", "track"),
    ):
        op.execute(
            sa.text(
                f"UPDATE {table} SET owner_fields = CASE WHEN user_id IS NOT NULL THEN '[\"metadata\"]'::jsonb ELSE '[]'::jsonb END"
            )
        )
        op.execute(
            sa.text(
                f"UPDATE {table} SET owner_fields = owner_fields || '[\"genres\"]'::jsonb WHERE user_id IS NOT NULL AND EXISTS (SELECT 1 FROM {kind}_genres WHERE {kind}_id = {table}.id)"
            )
        )
    op.execute(
        sa.text(
            "UPDATE tracks SET owner_fields = owner_fields || '[\"lyrics\"]'::jsonb WHERE user_id IS NOT NULL AND lyrics IS NOT NULL"
        )
    )


def downgrade() -> None:
    # Дополнительные виды предложений отсутствуют в предыдущей версии схемы.
    op.execute(
        "DELETE FROM contributions WHERE target_type IN ('venue','event') OR field = 'metadata'"
    )
    op.drop_constraint(
        op.f("ck_contributions_target_consistent"), "contributions", type_="check"
    )
    op.drop_constraint(
        op.f("ck_contributions_field_valid"), "contributions", type_="check"
    )
    from APP.models.base import target_constraint

    op.create_check_constraint(
        "target_consistent",
        "contributions",
        target_constraint("target_type", "target_id", ("track", "album", "artist")),
    )
    op.create_check_constraint(
        "field_valid",
        "contributions",
        "field IN ('lyrics','genres') AND (field != 'lyrics' OR target_type = 'track')",
    )
    for table in ("events", "venues"):
        op.drop_constraint(
            op.f("ck_" + table + "_publication_status_valid"), table, type_="check"
        )
    op.drop_index(op.f("ix_venues_publication_status"), table_name="venues")
    op.drop_column("venues", "publication_status")
    op.drop_column("users", "scene_verified")
    op.drop_column("tracks", "owner_fields")
    op.drop_index(op.f("ix_events_publication_status"), table_name="events")
    op.drop_column("events", "publication_status")
    op.drop_constraint(
        op.f("fk_contributions_venue_id_venues"), "contributions", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_contributions_event_id_events"), "contributions", type_="foreignkey"
    )
    op.drop_column("contributions", "event_id")
    op.drop_column("contributions", "venue_id")
    op.drop_column("artists", "owner_fields")
    op.drop_column("albums", "owner_fields")
    op.drop_table("contribution_votes")
    op.drop_table("event_attendance")
    op.drop_table("review_reward_texts")
