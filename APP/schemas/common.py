# APP/schemas/common.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class TimestampMixin(BaseModel):
    created_at: datetime