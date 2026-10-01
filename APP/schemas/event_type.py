from APP.schemas.common import BaseSchema


class EventType(BaseSchema):
    id: int
    name: str
    slug: str
