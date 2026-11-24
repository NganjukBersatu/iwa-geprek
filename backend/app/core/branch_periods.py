"""Satu pintu periode tutup buku per cabang: periode tersimpan bertanggal lengkap, dan bulan yang belum tersimpan mengikuti pola patokan, termasuk bulan sebelum patokan itu."""
import calendar
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import local_date
from app.core.errors import DomainError
from app.models.branch_period import BranchPeriod
from app.models.cash_session import CashSession
from app.models.ingredient import IngredientCount
from app.models.outlet import Outlet

# Daftar yang dipilih di laporan: periode berjalan ditambah sebelas sebelumnya, setahun penuh.
HISTORY_PERIODS = 12
MONTHS_PER_YEAR = 12
ONE_DAY = timedelta(days=1)
# Cabang yang belum pernah diatur memakai bulan kalender.
DEFAULT_PATTERN = (1, 31)

NOT_FOUND = 404
CONFLICT = 409
OUTLET_NOT_FOUND = "Cabang tidak ditemukan"
END_BEFORE_START = "Tanggal akhir periode tidak boleh sebelum tanggal mulai"
OVERLAPS_SAVED = "Rentang ini menimpa periode {start} sampai {end} yang sudah diatur; ubah periode itu dulu"
PERIOD_NOT_FOUND = "Periode ini sudah berubah; muat ulang halaman lalu coba lagi"
PERIOD_NOT_ADJUSTED = "Periode ini belum pernah diubah, jadi sudah mengikuti pola cabang"
PATTERN_LOCKED = "Periode ini menjadi patokan pola periode sesudahnya; ganti polanya lewat pengaturan Cabang"


@dataclass(frozen=True)
class Period:
    start: date
    end: date
    adjusted: bool
    sets_pattern: bool


@dataclass(frozen=True)
class _Anchor:
    month: tuple[int, int]
    pattern: tuple[int, int]


def _on_day(year: int, month: int, day: int) -> date:
    """Tanggal yang tidak ada di bulan itu (31 di Februari) menjadi hari terakhirnya."""
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def _month_after(year: int, month: int, months: int) -> tuple[int, int]:
    index = year * MONTHS_PER_YEAR + (month - 1) + months
    return index // MONTHS_PER_YEAR, index % MONTHS_PER_YEAR + 1


def _pattern_for(month: tuple[int, int], anchors: list[_Anchor]) -> tuple[int, int]:
    """Pola bulan itu datang dari patokan terakhir yang mulai pada atau sebelum bulan itu; bulan sebelum patokan pertama ikut patokan pertama."""
    if not anchors:
        return DEFAULT_PATTERN
    chosen = anchors[0].pattern
    for anchor in anchors:
        if anchor.month <= month:
            chosen = anchor.pattern
    return chosen


def _cycles(anchors: list[_Anchor], first: tuple[int, int], count: int) -> list[Period]:
    """Satu siklus per bulan menurut polanya; tanggal akhir sebelum tanggal mulai berarti siklus menyeberang ke bulan berikutnya."""
    cycles: list[Period] = []
    for offset in range(count):
        year, month = _month_after(*first, offset)
        start_day, end_day = _pattern_for((year, month), anchors)
        start = _on_day(year, month, start_day)
        end = _on_day(*_month_after(year, month, 1), end_day) if end_day < start_day else _on_day(year, month, end_day)
        # Pemepetan ke akhir bulan atau pergantian pola bisa membuat dua siklus berbagi hari; hari itu milik siklus sebelumnya.
        if cycles and start <= cycles[-1].end:
            start = cycles[-1].end + ONE_DAY
        if start <= end:
            cycles.append(Period(start, end, adjusted=False, sets_pattern=False))
    return cycles


def _outside(cycle: Period, saved: list[Period]) -> list[Period]:
    """Bagian siklus yang tidak tertutup periode tersimpan."""
    pieces = [cycle]
    for period in saved:
        remaining: list[Period] = []
        for piece in pieces:
            if period.end < piece.start or period.start > piece.end:
                remaining.append(piece)
                continue
            if piece.start < period.start:
                remaining.append(Period(piece.start, period.start - ONE_DAY, adjusted=False, sets_pattern=False))
            if piece.end > period.end:
                remaining.append(Period(period.end + ONE_DAY, piece.end, adjusted=False, sets_pattern=False))
        pieces = remaining
    return pieces


def _window(today: date) -> tuple[tuple[int, int], int]:
    """Dari siklus sedikit sebelum periode tertua yang didaftar sampai siklus sesudah periode berjalan."""
    return _month_after(today.year, today.month, -(HISTORY_PERIODS + 1)), HISTORY_PERIODS + 3


def _since(today: date) -> date:
    first, _ = _window(today)
    return date(first[0], first[1], 1)


def _anchor_of(row: BranchPeriod) -> _Anchor | None:
    if row.pattern_start_day is None or row.pattern_end_day is None:
        return None
    return _Anchor((row.start_date.year, row.start_date.month), (row.pattern_start_day, row.pattern_end_day))


def _period_of(row: BranchPeriod) -> Period:
    return Period(row.start_date, row.end_date, adjusted=True, sets_pattern=row.pattern_start_day is not None)


def _timeline(rows: list[BranchPeriod], today: date) -> list[Period]:
    """Periode tersimpan ditambah siklus pola di sela-selanya, urut menurut tanggal mulai."""
    anchors = sorted((anchor for anchor in map(_anchor_of, rows) if anchor is not None), key=lambda anchor: anchor.month)
    saved = [_period_of(row) for row in rows]
    first, count = _window(today)
    generated = [piece for cycle in _cycles(anchors, first, count) for piece in _outside(cycle, saved)]
    return sorted([*saved, *generated], key=lambda period: period.start)


def _rows_by_outlet(db: Session, outlet_ids: list[str], since: date) -> dict[str, list[BranchPeriod]]:
    """Periode tersimpan di jendela daftar, ditambah patokan terakhir sebelum jendela karena polanya masih berlaku; dua query untuk semua cabang."""
    grouped: dict[str, list[BranchPeriod]] = defaultdict(list)
    earlier = db.scalars(
        select(BranchPeriod)
        .where(BranchPeriod.outlet_id.in_(outlet_ids), BranchPeriod.end_date < since, BranchPeriod.pattern_start_day.is_not(None))
        .distinct(BranchPeriod.outlet_id)
        .order_by(BranchPeriod.outlet_id, BranchPeriod.start_date.desc())
    ).all()
    recent = db.scalars(
        select(BranchPeriod)
        .where(BranchPeriod.outlet_id.in_(outlet_ids), BranchPeriod.end_date >= since)
        .order_by(BranchPeriod.outlet_id, BranchPeriod.start_date)
    ).all()
    for row in [*earlier, *recent]:
        grouped[row.outlet_id].append(row)
    return grouped


def _opened_on(db: Session, outlet: Outlet, rows: list[BranchPeriod]) -> date:
    """Hari paling awal yang diketahui dari cabang: data impor bisa lebih baru dari operasinya, jadi tanggal dibuat dibandingkan dengan sesi kas pertama, periode tersimpan paling awal, dan penutupan stok pertama."""
    days = [local_date(outlet.created_at)]
    first_session = db.scalar(select(func.min(CashSession.opened_at)).where(CashSession.outlet_id == outlet.id))
    if first_session is not None:
        days.append(local_date(first_session))
    days.extend(row.start_date for row in rows)
    first_count = db.scalar(select(func.min(IngredientCount.period_start)).where(IngredientCount.outlet_id == outlet.id))
    if first_count is not None:
        days.append(first_count)
    return min(days)


def listing(db: Session, outlets: list[Outlet], today: date) -> dict[str, list[Period]]:
    """Per cabang, periode yang sudah mulai dan tidak berakhir sebelum hari paling awal cabang, dengan yang terbaru paling atas."""
    rows = _rows_by_outlet(db, [outlet.id for outlet in outlets], _since(today))
    result: dict[str, list[Period]] = {}
    for outlet in outlets:
        opened = _opened_on(db, outlet, rows.get(outlet.id, []))
        started = [period for period in _timeline(rows.get(outlet.id, []), today) if period.start <= today and period.end >= opened]
        result[outlet.id] = list(reversed(started[-HISTORY_PERIODS:]))
    return result


def _locked_rows(db: Session, outlet_id: str) -> list[BranchPeriod]:
    """Dua admin yang mengubah periode satu cabang bersamaan dibuat bergiliran supaya tidak saling menimpa."""
    if db.scalar(select(Outlet.id).where(Outlet.id == outlet_id).with_for_update()) is None:
        raise DomainError(OUTLET_NOT_FOUND, status=NOT_FOUND)
    return list(db.scalars(select(BranchPeriod).where(BranchPeriod.outlet_id == outlet_id).order_by(BranchPeriod.start_date)).all())


def _move(db: Session, outlet_id: str, rows: list[BranchPeriod], timeline: list[Period], index: int, start: date, end: date, *, carry_following: bool) -> BranchPeriod:
    """Memindah satu periode; tetangga yang menempel ikut bergeser supaya tidak ada hari tanpa periode."""
    if end < start:
        raise DomainError(END_BEFORE_START)
    original = timeline[index]
    previous = timeline[index - 1] if index > 0 else None
    following = timeline[index + 1] if index + 1 < len(timeline) else None
    by_start = {row.start_date: row for row in rows}

    for row in rows:
        if row.start_date == original.start or row.end_date < start or row.start_date > end:
            continue
        if previous and row.start_date == previous.start and start > row.start_date:
            continue
        if following and row.start_date == following.start and end < row.end_date:
            continue
        raise DomainError(OVERLAPS_SAVED.format(start=row.start_date.isoformat(), end=row.end_date.isoformat()), status=CONFLICT)

    # Tetangga yang tertelan seluruhnya hanya mungkin siklus pola (yang tersimpan sudah ditolak di atas), jadi cukup dilewati.
    touches_previous = previous is not None and (previous.end + ONE_DAY == original.start or previous.end >= start)
    if previous and touches_previous and start > previous.start and previous.end != start - ONE_DAY:
        _put(db, outlet_id, by_start.get(previous.start), previous.start, start - ONE_DAY)
    if following and end < following.end and following.start != end + ONE_DAY:
        # Saat pola diganti, siklus sesudahnya dibentuk ulang oleh pola baru; hanya periode tersimpan yang tertimpa yang perlu dipotong.
        overlapped = following.adjusted and following.start <= end
        touching = original.end + ONE_DAY == following.start or following.start <= end
        if overlapped or (carry_following and touching):
            _put(db, outlet_id, by_start.get(following.start), end + ONE_DAY, following.end)
    return _put(db, outlet_id, by_start.get(original.start), start, end)


def _put(db: Session, outlet_id: str, row: BranchPeriod | None, start: date, end: date) -> BranchPeriod:
    if row is None:
        row = BranchPeriod(outlet_id=outlet_id, start_date=start, end_date=end)
        db.add(row)
    else:
        row.start_date = start
        row.end_date = end
    # Satu flush per baris supaya batas UNIQUE (cabang, tanggal mulai) diperiksa pada urutan yang sudah benar.
    db.flush()
    return row


def adjust(db: Session, outlet_id: str, original_start: date, start: date, end: date, today: date) -> None:
    """Menggeser satu periode saja; pola periode sesudahnya tidak berubah. Pemanggil yang menyimpan transaksinya."""
    rows = _locked_rows(db, outlet_id)
    timeline = _timeline(rows, today)
    index = next((position for position, period in enumerate(timeline) if period.start == original_start), None)
    if index is None:
        raise DomainError(PERIOD_NOT_FOUND, status=NOT_FOUND)
    _move(db, outlet_id, rows, timeline, index, start, end, carry_following=True)


def set_pattern(db: Session, outlet_id: str, start: date, end: date) -> None:
    """Menetapkan pola cabang untuk semua periode, yang lama maupun yang akan datang, dengan periode ini sebagai patokannya; pergeseran per bulan sebelumnya ikut dihapus. Pemanggil yang menyimpan transaksinya."""
    if end < start:
        raise DomainError(END_BEFORE_START)
    rows = _locked_rows(db, outlet_id)
    for row in rows:
        db.delete(row)
    db.flush()
    row = _put(db, outlet_id, None, start, end)
    row.pattern_start_day = start.day
    row.pattern_end_day = end.day
    db.flush()


def reset(db: Session, outlet_id: str, start: date) -> None:
    """Mengembalikan periode yang digeser ke pola cabang. Pemanggil yang menyimpan transaksinya."""
    row = next((row for row in _locked_rows(db, outlet_id) if row.start_date == start), None)
    if row is None:
        raise DomainError(PERIOD_NOT_ADJUSTED, status=NOT_FOUND)
    if row.pattern_start_day is not None:
        raise DomainError(PATTERN_LOCKED, status=CONFLICT)
    db.delete(row)
    db.flush()
