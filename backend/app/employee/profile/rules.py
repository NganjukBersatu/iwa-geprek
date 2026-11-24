"""Clean-up and checks for the personal data an employee types in."""
from datetime import date

from app.core.clock import today
from app.employee.profile import messages
from app.employee.profile.constants import EMAIL_PATTERN, GENDERS, OLDEST_BIRTH_YEAR, PHONE_PATTERN


def tidy(value):
    """Words are separated by single spaces, and an empty entry counts as not filled in."""
    if isinstance(value, str):
        return " ".join(value.split()) or None
    return value


def check_phone(value: str | None) -> str | None:
    if value is not None and not PHONE_PATTERN.match(value):
        raise ValueError(messages.INVALID_PHONE)
    return value


def check_email(value: str | None) -> str | None:
    if value is not None and not EMAIL_PATTERN.match(value):
        raise ValueError(messages.INVALID_EMAIL)
    return value


def check_birth_date(value: date | None) -> date | None:
    if value is not None and not (date(OLDEST_BIRTH_YEAR, 1, 1) <= value < today()):
        raise ValueError(messages.INVALID_BIRTH_DATE)
    return value


def check_gender(value: str | None) -> str | None:
    if value is not None and value not in GENDERS:
        raise ValueError(messages.INVALID_GENDER)
    return value
