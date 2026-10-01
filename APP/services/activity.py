from sqlalchemy.ext.asyncio import AsyncSession

from APP.models.event_log import EventLog


def record_event(
    session: AsyncSession,
    user_id: int,
    action: str,
    kind: str,
    target_id: int,
    *,
    public: bool = True,
    payload: dict | None = None,
) -> None:
    session.add(
        EventLog(
            actor_id=user_id,
            action=action,
            target_type=kind,
            target_id=target_id,
            payload=payload or {},
            is_public=public,
        )
    )
