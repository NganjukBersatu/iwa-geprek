from datetime import date, datetime

from pydantic import BaseModel, Field

from app.core.password_policy import MAX_PASSWORD_LENGTH
from app.employee.profile.schemas import PersonalDataIn
from web.management.users.constants import MAX_NAME_LENGTH, MAX_USERNAME_LENGTH


class UserCreateIn(PersonalDataIn):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    username: str = Field(min_length=1, max_length=MAX_USERNAME_LENGTH)
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)
    role_id: str
    outlet_id: str | None = Field(None, description="Required unless the role has full access; checked in the service")
    joined_date: date | None = None


class UserUpdateIn(PersonalDataIn):
    """A field left out stays as it was; a new password resets it without asking for the old one."""

    name: str | None = Field(None, min_length=1, max_length=MAX_NAME_LENGTH)
    username: str | None = Field(None, min_length=1, max_length=MAX_USERNAME_LENGTH)
    password: str | None = Field(None, min_length=1, max_length=MAX_PASSWORD_LENGTH)
    role_id: str | None = None
    outlet_id: str | None = None
    is_active: bool | None = None
    joined_date: date | None = None


class UserOut(BaseModel):
    id: str
    name: str | None
    username: str
    role_id: str
    role_name: str
    permissions: list[str]
    outlet_id: str | None
    is_active: bool
    created_at: datetime | None
    photo_url: str | None
    phone: str | None
    address: str | None
    birth_date: date | None
    gender: str | None
    email: str | None
    emergency_name: str | None
    emergency_phone: str | None
    emergency_relation: str | None
    joined_date: date | None
    locked: bool = Field(description="True when the viewer may not change, reset or delete this account")


class UserPageOut(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    size: int
