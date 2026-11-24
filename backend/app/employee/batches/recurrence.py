"""Pola berulang tugas rutin dan tugas outlet: pada hari apa sebuah templat berlaku."""
import calendar
from datetime import date

from app.employee.batches.constants import WEEKDAY_SEPARATOR
from app.models.outlet_batch import UNIT_DAY, UNIT_MONTH, UNIT_WEEK, OutletBatch

DAYS_IN_WEEK = 7
MONTHS_IN_YEAR = 12
# Batas atas "ulangi setiap" per satuan: setahun dalam hari, minggu, dan bulan.
MAX_EVERY = {UNIT_DAY: 365, UNIT_WEEK: 52, UNIT_MONTH: 12}


def numbers_of(joined: str | None) -> set[int]:
    """Angka yang disimpan berjajar dengan koma, seperti hari dalam minggu pada templat lama."""
    return {int(part) for part in joined.split(WEEKDAY_SEPARATOR)} if joined else set()


def applies_on(batch: OutletBatch, day: date) -> bool:
    """Berulang tiap N hari, minggu, atau bulan dari tanggal mulainya; templat lama tanpa satuan tetap mengikuti hari terpilihnya."""
    if batch.repeat_unit is None or batch.starts_on is None:
        weekdays = numbers_of(batch.weekdays)
        return not weekdays or day.weekday() in weekdays
    return occurs(batch.repeat_unit, batch.repeat_every, batch.starts_on, day)


def occurs(unit: str, every: int, start: date, day: date) -> bool:
    if day < start:
        return False
    if unit == UNIT_MONTH:
        months = (day.year - start.year) * MONTHS_IN_YEAR + day.month - start.month
        return months % every == 0 and day.day == _day_in_month(start.day, day)
    span = every * DAYS_IN_WEEK if unit == UNIT_WEEK else every
    return (day - start).days % span == 0


def _day_in_month(wanted: int, day: date) -> int:
    """Tanggal yang tidak ada di bulan itu, misalnya 31 di bulan 30 hari, jatuh ke hari terakhir bulan."""
    return min(wanted, calendar.monthrange(day.year, day.month)[1])
