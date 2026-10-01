from typing import Annotated, Literal

from pydantic import EmailStr, Field, SecretStr, field_validator

from APP.core.constants import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH
from APP.schemas.common import BaseSchema, InputSchema, NonEmptyText, PositiveInteger

Password = Annotated[
    SecretStr, Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
]
RefreshToken = Annotated[SecretStr, Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)]


class LoginInput(InputSchema):
    email: EmailStr
    password: Password

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class RegisterInput(LoginInput):
    display_name: NonEmptyText


class RefreshInput(InputSchema):
    refresh_token: RefreshToken


class TokenPair(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: PositiveInteger
    refresh_expires_in: PositiveInteger
