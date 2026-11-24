"""Kecocokan kategori dengan kode shift; jenis dan rentang jamnya diatur admin di kategori, bukan ditulis di kode."""
from app.core.errors import DomainError
from app.employee.schedule.window import minutes_of_day
from app.models.category import Category
from web.management.shift_codes import messages
from web.management.shift_codes.constants import CODE_CLOCK_MISMATCH, CODE_KIND_MISMATCH, KIND_OFF, KIND_WORK


def starts_within(start_clock: str, from_clock: str, until_clock: str) -> bool:
    """Rentang yang selesai lebih awal dari mulainya melewati tengah malam, seperti jam kode shift."""
    start, begin, end = minutes_of_day(start_clock), minutes_of_day(from_clock), minutes_of_day(until_clock)
    if begin <= end:
        return begin <= start <= end
    return start >= begin or start <= end


def violation(category: Category, *, is_day_off: bool, start_clock: str | None) -> DomainError | None:
    """Kategori tanpa jenis atau rentang tidak memeriksa apa pun, sehingga aturan baru berlaku hanya sesuai yang diatur admin."""
    if category.shift_kind == KIND_OFF and not is_day_off:
        return DomainError(messages.WORK_CODE_ON_OFF_CATEGORY.format(category=category.name), code=CODE_KIND_MISMATCH, field="category")
    if category.shift_kind == KIND_WORK and is_day_off:
        return DomainError(messages.OFF_CODE_ON_WORK_CATEGORY.format(category=category.name), code=CODE_KIND_MISMATCH, field="category")
    if is_day_off or not start_clock or not category.shift_start_from or not category.shift_start_until:
        return None
    if starts_within(start_clock, category.shift_start_from, category.shift_start_until):
        return None
    return DomainError(
        messages.START_OUTSIDE_CATEGORY.format(
            start=start_clock, category=category.name, begin=category.shift_start_from, end=category.shift_start_until
        ),
        code=CODE_CLOCK_MISMATCH,
        field="start_clock",
    )


def ensure_matches(category: Category, *, is_day_off: bool, start_clock: str | None) -> None:
    problem = violation(category, is_day_off=is_day_off, start_clock=start_clock)
    if problem is not None:
        raise problem
