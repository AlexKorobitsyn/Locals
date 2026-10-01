from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from APP.core.constants import ROLE_MAX_LENGTH
from APP.models.base import Base


class EventLog(Base):
    __tablename__ = "event_logs"
    __table_args__ = (
        CheckConstraint("length(btrim(action)) > 0", name="action_nonempty"),
        CheckConstraint("length(btrim(target_type)) > 0", name="target_type_nonempty"),
        CheckConstraint("target_id > 0", name="target_id_positive"),
        CheckConstraint("jsonb_typeof(payload) = 'object'", name="payload_object"),
        Index("ix_event_logs_actor_created_at", "actor_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(ROLE_MAX_LENGTH))
    target_type: Mapped[str] = mapped_column(String(ROLE_MAX_LENGTH))
    target_id: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
