"""Aturan jam kode shift: jam selesai harus jelas, dan shift yang berakhir di hari berikutnya hanya diterima bila dinyatakan sengaja."""
from app.core.errors import DomainError
from app.employee.schedule.constants import MINUTES_PER_DAY, MINUTES_PER_HOUR
from app.employee.schedule.window import clock_minutes
from web.management.shift_codes import messages
from web.management.shift_codes.constants import (
    CODE_MIDNIGHT_UNNEEDED,
    CODE_NEEDS_MIDNIGHT,
    CODE_SHIFT_SAME_CLOCK,
    CODE_SHIFT_TOO_LONG,
    CODE_START_AT_24,
    MAX_SHIFT_MINUTES,
    PROBLEM_SAME,
    PROBLEM_TOO_LONG,
)


def _length_text(minutes: int) -> str:
    hours, rest = divmod(minutes, MINUTES_PER_HOUR)
    return f"{hours} jam {rest} menit" if rest else f"{hours} jam"


def problem(start_clock: str | None, end_clock: str | None) -> str | None:
    """Kode yang sudah tersimpan: jam yang tidak wajar tanpa memandang tanda; kode lama yang melewati tengah malam tidak dianggap masalah."""
    if not start_clock or not end_clock:
        return None
    start, end = clock_minutes(start_clock), clock_minutes(end_clock)
    if end == start:
        return PROBLEM_SAME
    length = (end - start) % MINUTES_PER_DAY
    return PROBLEM_TOO_LONG if length > MAX_SHIFT_MINUTES else None


def ensure_valid(start_clock: str, end_clock: str, *, crosses_midnight: bool) -> None:
    """Jam selesai lebih awal dari jam mulai berarti hari berikutnya, dan itu hanya diterima bila [crosses_midnight] benar."""
    start, end = clock_minutes(start_clock), clock_minutes(end_clock)
    if start >= MINUTES_PER_DAY:
        raise DomainError(messages.START_AT_24, code=CODE_START_AT_24, field="start_clock")
    if end == start:
        raise DomainError(messages.END_SAME_AS_START.format(end=end_clock), code=CODE_SHIFT_SAME_CLOCK, field="end_clock")
    overnight = end < start
    if overnight and not crosses_midnight:
        raise DomainError(messages.NEEDS_MIDNIGHT.format(start=start_clock, end=end_clock), code=CODE_NEEDS_MIDNIGHT, field="crosses_midnight")
    if crosses_midnight and not overnight:
        raise DomainError(messages.MIDNIGHT_UNNEEDED.format(start=start_clock, end=end_clock), code=CODE_MIDNIGHT_UNNEEDED, field="crosses_midnight")
    length = end - start + (MINUTES_PER_DAY if overnight else 0)
    if length > MAX_SHIFT_MINUTES:
        raise DomainError(
            messages.SHIFT_TOO_LONG.format(length=_length_text(length), maximum=_length_text(MAX_SHIFT_MINUTES)),
            code=CODE_SHIFT_TOO_LONG,
            field="end_clock",
        )
