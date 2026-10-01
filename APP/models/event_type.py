from sqlalchemy import Identity, String
from sqlalchemy.orm import Mapped, mapped_column

from APP.core.constants import NAME_MAX_LENGTH, SLUG_MAX_LENGTH
from APP.models.base import Base


class EventType(Base):
    __tablename__ = "event_types"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    slug: Mapped[str] = mapped_column(String(SLUG_MAX_LENGTH), unique=True)
