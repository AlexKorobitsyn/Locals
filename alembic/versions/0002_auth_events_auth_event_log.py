"""Непубличные события авторизации.

Revision ID: 0002_auth_events
Revises: 0001_catalog_auth
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0002_auth_events"
down_revision = "0001_catalog_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_logs",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("is_public", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "jsonb_typeof(payload) = 'object'",
            name=op.f("ck_event_logs_payload_object"),
        ),
        sa.CheckConstraint(
            "length(btrim(action)) > 0", name=op.f("ck_event_logs_action_nonempty")
        ),
        sa.CheckConstraint(
            "length(btrim(target_type)) > 0",
            name=op.f("ck_event_logs_target_type_nonempty"),
        ),
        sa.CheckConstraint(
            "target_id > 0", name=op.f("ck_event_logs_target_id_positive")
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_event_logs_actor_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_logs")),
    )
    op.create_index(
        "ix_event_logs_actor_created_at",
        "event_logs",
        ["actor_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_event_logs_actor_created_at", table_name="event_logs")
    op.drop_table("event_logs")
