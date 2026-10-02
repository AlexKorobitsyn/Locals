from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import AnyHttpUrl, EmailStr, Field, field_validator

from APP.core.constants import BIO_MAX_LENGTH
from APP.schemas.common import InputSchema, NonEmptyText, PositiveId
from APP.schemas.user import UserMe


class AdminUserOut(UserMe):
    is_active: bool
    weight: Decimal
    updated_at: datetime


class UserLevelPut(InputSchema):
    level: Literal["green", "experienced", "moderator"]


class UserStatusPut(InputSchema):
    is_active: bool = Field(strict=True)


class AdminUserUpdate(InputSchema):
    display_name: NonEmptyText | None = None
    email: EmailStr | None = None
    bio: str | None = Field(default=None, max_length=BIO_MAX_LENGTH)
    city_id: PositiveId | None = None
    avatar_url: AnyHttpUrl | None = None

    @field_validator("display_name", "email")
    @classmethod
    def required_if_present(cls, value):
        if value is None:
            raise ValueError("field cannot be null")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return str(value).lower()


class ModeratedProfileUpdate(InputSchema):
    display_name: NonEmptyText | None = None
    bio: str | None = Field(default=None, max_length=BIO_MAX_LENGTH)
    city_id: PositiveId | None = None
    avatar_url: AnyHttpUrl | None = None

    @field_validator("display_name")
    @classmethod
    def required_if_present(cls, value):
        if value is None:
            raise ValueError("display_name cannot be null")
        return value


class SceneVerificationPut(InputSchema):
    scene_verified: bool = Field(strict=True)
