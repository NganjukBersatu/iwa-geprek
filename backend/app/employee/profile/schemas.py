from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.core.password_policy import MAX_PASSWORD_LENGTH
from app.employee.profile import rules
from app.employee.profile.constants import (
    MAX_ADDRESS_LENGTH,
    MAX_EMAIL_LENGTH,
    MAX_NAME_LENGTH,
    MAX_PHONE_LENGTH,
    MAX_RELATION_LENGTH,
)

PERSONAL_TEXT_FIELDS = ("phone", "address", "email", "gender", "emergency_name", "emergency_phone", "emergency_relation")
# Personal data an admin may also fill in from the user screen; both sides write the same columns.
PERSONAL_FIELDS = (*PERSONAL_TEXT_FIELDS, "birth_date")


class ProfileOut(BaseModel):
    name: str | None
    username: str
    role_name: str
    outlet_name: str | None
    joined_date: date | None
    birth_date: date | None
    phone: str | None
    address: str | None
    email: str | None
    gender: str | None
    emergency_name: str | None
    emergency_phone: str | None
    emergency_relation: str | None
    photo_url: str | None


class PersonalDataIn(BaseModel):
    """A field that is sent is changed, one that is left out stays, and one sent empty is cleared."""

    phone: str | None = Field(None, max_length=MAX_PHONE_LENGTH)
    address: str | None = Field(None, max_length=MAX_ADDRESS_LENGTH)
    birth_date: date | None = None
    gender: str | None = None
    email: str | None = Field(None, max_length=MAX_EMAIL_LENGTH)
    emergency_name: str | None = Field(None, max_length=MAX_NAME_LENGTH)
    emergency_phone: str | None = Field(None, max_length=MAX_PHONE_LENGTH)
    emergency_relation: str | None = Field(None, max_length=MAX_RELATION_LENGTH)

    @field_validator(*PERSONAL_TEXT_FIELDS, mode="before")
    @classmethod
    def _tidy(cls, value):
        return rules.tidy(value)

    @field_validator("phone", "emergency_phone")
    @classmethod
    def _phone(cls, value):
        return rules.check_phone(value)

    @field_validator("email")
    @classmethod
    def _email(cls, value):
        return rules.check_email(value)

    @field_validator("birth_date")
    @classmethod
    def _birth_date(cls, value):
        return rules.check_birth_date(value)

    @field_validator("gender")
    @classmethod
    def _gender(cls, value):
        return rules.check_gender(value)


class ProfileUpdateIn(PersonalDataIn):
    name: str | None = Field(None, max_length=MAX_NAME_LENGTH)

    @field_validator("name", mode="before")
    @classmethod
    def _tidy_name(cls, value):
        return rules.tidy(value)


class PasswordChangeIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)
    new_password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)
