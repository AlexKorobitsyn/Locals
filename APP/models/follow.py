from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Identity,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from APP.core.constants import FollowTarget
from APP.models.base import Base, TimestampMixin, target_constraint


class Follow(TimestampMixin, Base):
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "target_type", "target_id"),
        Index("ix_follows_target", "target_type", "target_id"),
        CheckConstraint("target_id > 0", name="target_id_positive"),
        CheckConstraint(
            "target_type <> 'user' OR follower_id <> target_id", name="no_self_follow"
        ),
        CheckConstraint(
            target_constraint(
                "target_type", "target_id", tuple(kind.value for kind in FollowTarget)
            ),
            name="target_consistent",
        ),
    )
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    target_type: Mapped[FollowTarget] = mapped_column(
        Enum(
            FollowTarget,
            name="follow_target",
            native_enum=False,
            create_constraint=True,
        )
    )
    target_id: Mapped[int] = mapped_column()
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    artist_id: Mapped[int | None] = mapped_column(
        ForeignKey("artists.id", ondelete="CASCADE"), index=True
    )
    venue_id: Mapped[int | None] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"), index=True
    )
