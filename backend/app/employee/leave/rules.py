"""Checks and clean-up of what an employee types into a leave request."""
from datetime import date

from app.core.errors import DomainError
from app.employee.leave import messages
from app.employee.leave.constants import LINK_SCHEMES, MAX_DAYS


def check_period(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise DomainError(messages.END_BEFORE_START)
    if (end_date - start_date).days + 1 > MAX_DAYS:
        raise DomainError(messages.TOO_LONG)


def clean_reason(reason: str) -> str:
    cleaned = reason.strip()
    if not cleaned:
        raise DomainError(messages.REASON_REQUIRED)
    return cleaned


def clean_link(link: str | None) -> str | None:
    cleaned = (link or "").strip()
    if not cleaned:
        return None
    if not cleaned.lower().startswith(LINK_SCHEMES):
        raise DomainError(messages.BAD_LINK)
    return cleaned
