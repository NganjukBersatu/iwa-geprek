"""Rules every report shares: the permission, branch filtering, date ranges, and percentages."""
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import today
from app.core.errors import DomainError
from app.core.money import ZERO, decimal_of
from app.models.user import User
from web.management.reports import messages


# A year is enough for any report; longer ranges hold the database for too long.
MAX_RANGE_DAYS = 366

CENT = Decimal("0.01")
TENTH = Decimal("0.1")


def as_http(error: DomainError) -> HTTPException:
    return HTTPException(status_code=error.status, detail=error.message)


def sum_of(db: Session, statement) -> Decimal:
    return decimal_of(db.scalar(statement))


def resolve_range(start: date | None, end: date | None) -> tuple[date, date]:
    """Completes a range; both empty means today."""
    if start is None and end is None:
        current = today()
        return current, current
    if start is None:
        start = end
    if end is None:
        end = start
    if end < start:
        raise DomainError(messages.END_BEFORE_START)
    return start, end


def from_today(start: date | None, end: date | None) -> tuple[date, date]:
    """A missing start means today and a missing end means the start."""
    start = start or today()
    end = end or start
    if end < start:
        raise DomainError(messages.END_BEFORE_START)
    return start, end


def ensure_max_range(start: date, end: date) -> None:
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise DomainError(messages.RANGE_TOO_LONG.format(days=MAX_RANGE_DAYS))


def month_to_date(start: date | None, end: date | None) -> tuple[date, date]:
    """Both empty means the first of this month until today."""
    if start is None and end is None:
        current = today()
        return current.replace(day=1), current
    start, end = resolve_range(start, end)
    ensure_max_range(start, end)
    return start, end


def last_days(start: date | None, end: date | None, days: int) -> tuple[date, date]:
    """Both empty means the last `days` days up to today."""
    if start is None and end is None:
        end = today()
        return end - timedelta(days=days - 1), end
    start, end = resolve_range(start, end)
    ensure_max_range(start, end)
    return start, end


def percent(part: Decimal, total: Decimal) -> Decimal:
    """Two decimals; zero when the total is not positive."""
    if total <= 0:
        return Decimal("0.00")
    return (part / total * 100).quantize(CENT)


def percent_tenth(part: Decimal, total: Decimal) -> Decimal:
    """One decimal; zero only when the total is zero."""
    return (part * 100 / total).quantize(TENTH) if total else ZERO


def optional_percent(part, total) -> Decimal | None:
    """One decimal, or None when the total is not positive, for figures that have no meaning without a base."""
    total = decimal_of(total)
    if total <= 0:
        return None
    return (decimal_of(part) / total * 100).quantize(TENTH)


def divide(value: Decimal, divisor: int) -> Decimal:
    if divisor <= 0:
        return Decimal("0.00")
    return (value / Decimal(divisor)).quantize(CENT)


def user_usernames(db: Session, user_ids: set[str]) -> dict[str, str]:
    if not user_ids:
        return {}
    return dict(db.execute(select(User.id, User.username).where(User.id.in_(user_ids))).all())
