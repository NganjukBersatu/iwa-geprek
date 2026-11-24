"""Time helpers; the business runs on WIB, which has no daylight saving, so a fixed offset is exact."""
from datetime import date, datetime, timedelta, timezone

WIB_OFFSET_HOURS = 7
SECONDS_PER_MINUTE = 60
WIB = timezone(timedelta(hours=WIB_OFFSET_HOURS))


def now() -> datetime:
    return datetime.now(timezone.utc)


def local_date(instant: datetime) -> date:
    return as_aware(instant).astimezone(WIB).date()


def today() -> date:
    return local_date(now())


def minutes_between(start: datetime | None, end: datetime | None) -> int | None:
    """Whole minutes from start to end, never negative; None while either is missing."""
    if start is None or end is None:
        return None
    seconds = int((as_aware(end) - as_aware(start)).total_seconds())
    return max(0, seconds // SECONDS_PER_MINUTE)


def as_aware(instant: datetime) -> datetime:
    """Stored instants are UTC, so one without a zone is read as UTC."""
    return instant if instant.tzinfo is not None else instant.replace(tzinfo=timezone.utc)
