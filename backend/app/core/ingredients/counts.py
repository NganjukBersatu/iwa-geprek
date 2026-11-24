"""The one door for closing a stock count (opname): the web sheet and the tablet both record through here.

A count keeps what was physically there as a snapshot per ingredient, then starts the next period from zero: one reset card per
ingredient with stock brings every balance of the branch to 0, counted or not.
"""
from dataclasses import dataclass
from enum import StrEnum
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.orm import Session

from app.core.clock import today
from app.core.date_range import range_end
from app.core import branch_periods, stock_balances
from app.core.errors import DomainError
from app.core.ingredients import count_drafts, count_requests, messages
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.outlet import Outlet
from app.models.ingredient import INGREDIENT_ADJUSTMENT, OPENING_CAUSE, OPENING_NOTE_PREFIX, Ingredient, IngredientCard, IngredientCount, IngredientCountLine
from app.models.user import User

NOT_FOUND = 404
CONFLICT = 409
LOCK_PREFIX = "ingredient-count:"
SOURCE_WEB = "web"
SOURCE_TABLET = "tablet"
RESET_LABEL = "Reset ke 0 · Opname {start:%d/%m}–{end:%d/%m/%Y}"


@dataclass(frozen=True)
class BookedLine:
    """One counted ingredient: what the books said, what was counted, and the price and tolerance in force at that moment."""

    ingredient_id: str
    name: str
    book_balance: Decimal
    counted: Decimal
    unit_price: Decimal
    shrink_tolerance: Decimal


def closed_for(db: Session, outlet_id: str, start: date, end: date) -> bool:
    found = db.scalar(select(IngredientCount.id).where(IngredientCount.outlet_id == outlet_id, IngredientCount.period_start == start, IngredientCount.period_end == end))
    return found is not None


def lock_branch(db: Session, outlet_id: str) -> None:
    """Penutupan di satu cabang berjalan bergantian sampai commit, supaya dua penutupan bersamaan tidak sama-sama lolos pemeriksaan."""
    # Fungsi kunci mengembalikan void yang tidak bisa dibaca driver, jadi yang dibaca hanya angka 1.
    db.execute(text("SELECT 1 FROM pg_advisory_xact_lock(hashtext(:key))"), {"key": LOCK_PREFIX + outlet_id})


def ensure_closable(db: Session, outlet_id: str, start: date, end: date) -> None:
    """The end of a period may not lie in the future, since a movement arriving afterwards would change a closed period; one period closes once per branch."""
    if end < start:
        raise DomainError(messages.END_BEFORE_START)
    if end > today():
        raise DomainError(messages.PERIOD_NOT_OVER)
    lock_branch(db, outlet_id)
    if closed_for(db, outlet_id, start, end):
        raise DomainError(messages.ALREADY_CLOSED, status=CONFLICT)
    overlapping = db.scalar(
        select(IngredientCount.id).where(IngredientCount.outlet_id == outlet_id, IngredientCount.period_start <= end, IngredientCount.period_end >= start).limit(1)
    )
    if overlapping is not None:
        raise DomainError(messages.PERIOD_OVERLAPS, status=CONFLICT)
    if open_sessions(db, outlet_id, end) > 0:
        raise DomainError(messages.SESSION_STILL_OPEN, status=CONFLICT)


def open_sessions(db: Session, outlet_id: str, end: date) -> int:
    """Sesi kasir yang masih berjalan dengan hari bisnis sampai tanggal akhir: penjualannya akan jatuh ke periode yang sudah ditutup."""
    return db.scalar(
        select(func.count()).select_from(CashSession).where(CashSession.outlet_id == outlet_id, CashSession.status == CashSessionStatus.OPEN, CashSession.business_day <= end)
    ) or 0


def _is_opening_marker():
    """Kartu stok awal bukan pergerakan stok: dicap sedetik sebelum periode, jadi bila ikut dihitung ia menggeser hari pergerakan pertama satu hari ke belakang dan periodenya tidak lagi cocok dengan penandanya."""
    return and_(
        IngredientCard.kind == INGREDIENT_ADJUSTMENT,
        IngredientCard.count_id.is_(None),
        or_(IngredientCard.cause == OPENING_CAUSE, IngredientCard.note.like(OPENING_NOTE_PREFIX + "%")),
    )


def first_movement_days(db: Session, outlet_ids: list[str]) -> dict[str, date]:
    """Hari bisnis pergerakan bahan pertama tiap cabang; satu bacaan berurutan per cabang lewat indeks (cabang, waktu) dan berhenti di baris pertama, bukan memindai seluruh kartu.

    Kartu stok awal di kepala urutan hanya ada selama cabang belum menutup periode dan jumlahnya paling banyak sebanyak bahannya (bukan sebanyak datanya),
    jadi tidak dibuatkan indeks parsial: indeks tambahan memperlambat setiap tulis kartu bahan, sedangkan biaya baca ini terbatas.
    """
    found: dict[str, date] = {}
    for outlet_id in outlet_ids:
        day = db.scalar(
            select(IngredientCard.business_day).where(IngredientCard.outlet_id == outlet_id, ~_is_opening_marker()).order_by(IngredientCard.created_at, IngredientCard.id).limit(1)
        )
        if day is not None:
            found[outlet_id] = day
    return found


def running_starts(db: Session, outlet_ids: list[str]) -> dict[str, date]:
    """The first day of the period each branch is in now: the day after its last closed period, or the start of the branch period holding its first movement; a branch closed up to today has none.

    One source for every screen that says "periode berjalan": stock opening, goods in, waste, and expenses all start where the branch period starts.
    """
    if not outlet_ids:
        return {}
    last_ends = dict(
        db.execute(select(IngredientCount.outlet_id, func.max(IngredientCount.period_end)).where(IngredientCount.outlet_id.in_(outlet_ids)).group_by(IngredientCount.outlet_id)).all()
    )
    never = [outlet_id for outlet_id in outlet_ids if last_ends.get(outlet_id) is None]
    firsts = first_movement_days(db, never)
    listed = branch_periods.listing(db, list(db.scalars(select(Outlet).where(Outlet.id.in_(never)))), today()) if never else {}
    result: dict[str, date] = {}
    for outlet_id in outlet_ids:
        last_end = last_ends.get(outlet_id)
        if last_end is None:
            first = firsts.get(outlet_id) or today()
            holder = next((period for period in listed.get(outlet_id, []) if period.start <= first <= period.end), None)
            result[outlet_id] = holder.start if holder else first
        elif last_end < today():
            result[outlet_id] = last_end + timedelta(days=1)
    return result


class OpenState(StrEnum):
    # Pergerakan sebelum periode yang harus ditutup; ikut menjadi stok awal periode itu.
    OPENING = "opening"
    TO_CLOSE = "to_close"
    RUNNING = "running"
    # Seperti OPENING, tetapi penutupan yang menampungnya sudah terjadi; tampil di antara riwayat yang sudah ditutup.
    ABSORBED = "absorbed"


@dataclass(frozen=True)
class OpenPiece:
    """Bagian waktu yang belum ditutup, dipotong menurut periode cabang; end kosong berarti sampai hari ini."""

    start: date
    end: date | None
    state: OpenState
    period_start: date
    period_end: date


def _closing_range(periods: list[branch_periods.Period], last_end: date | None, now: date, first_movement: date | None = None) -> tuple[date, date]:
    """Periode cabang terakhir yang sudah selesai dan belum ditutup; bila tidak ada, periode berjalan sampai hari ini.

    Cabang yang belum pernah menutup periode mulai dari hari pergerakan stok pertamanya (sama dengan stok awal periode berjalan), bukan dari awal periode kalender.
    """
    ended = next((period for period in periods if period.end < now and (last_end is None or period.end > last_end) and (first_movement is None or period.end >= first_movement)), None)
    if ended is not None:
        start = ended.start if last_end is None or ended.start > last_end else last_end + timedelta(days=1)
        return max(start, first_movement) if first_movement else start, ended.end
    running = next((period for period in periods if period.start <= now <= period.end), None)
    start = running.start if running else now
    if last_end is not None and start <= last_end:
        start = last_end + timedelta(days=1)
    if first_movement is not None:
        start = max(start, first_movement)
    return start, max(start, now)


def _last_ends(db: Session, outlet_ids: list[str]) -> dict[str, date]:
    if not outlet_ids:
        return {}
    return dict(db.execute(select(IngredientCount.outlet_id, func.max(IngredientCount.period_end)).where(IngredientCount.outlet_id.in_(outlet_ids)).group_by(IngredientCount.outlet_id)).all())


def closing_period(db: Session, outlet_id: str) -> tuple[date, date]:
    """Periode yang semestinya ditutup sekarang, dengan pergerakan sebelumnya menjadi stok awalnya; satu aturan untuk web dan pengajuan tablet."""
    outlet = db.get(Outlet, outlet_id)
    if outlet is None:
        raise DomainError(messages.OUTLET_NOT_FOUND, status=NOT_FOUND)
    now = today()
    periods = branch_periods.listing(db, [outlet], now).get(outlet_id, [])
    last_end = _last_ends(db, [outlet_id]).get(outlet_id)
    first_movement = running_starts(db, [outlet_id]).get(outlet_id) if last_end is None else None
    return _closing_range(periods, last_end, now, first_movement)


def _split(start: date, end: date, periods: list[branch_periods.Period], state: OpenState) -> list[OpenPiece]:
    """Memotong rentang menurut periode cabang yang dikenal; bagian di luar daftar periode tetap satu potong."""
    pieces: list[OpenPiece] = []
    cursor = start
    for period in sorted(periods, key=lambda item: item.start):
        if period.end < cursor or period.start > end:
            continue
        if period.start > cursor:
            pieces.append(OpenPiece(cursor, period.start - timedelta(days=1), state, cursor, period.start - timedelta(days=1)))
        piece_end = min(period.end, end)
        pieces.append(OpenPiece(max(cursor, period.start), piece_end, state, period.start, period.end))
        cursor = piece_end + timedelta(days=1)
    if cursor <= end:
        pieces.append(OpenPiece(cursor, end, state, cursor, end))
    return pieces


def absorbed_pieces(db: Session, outlets: list[Outlet]) -> dict[str, list[OpenPiece]]:
    """Bagian waktu yang tidak pernah ditutup sendiri karena masuk stok awal penutupan sesudahnya: sebelum penutupan pertama dan di sela dua penutupan."""
    ids = [outlet.id for outlet in outlets]
    if not ids:
        return {}
    firsts = first_movement_days(db, ids)
    closed: dict[str, list[tuple[date, date]]] = {}
    for outlet_id, start, end in db.execute(
        select(IngredientCount.outlet_id, IngredientCount.period_start, IngredientCount.period_end).where(IngredientCount.outlet_id.in_(ids)).order_by(IngredientCount.outlet_id, IngredientCount.period_start)
    ).all():
        closed.setdefault(outlet_id, []).append((start, end))
    listed = branch_periods.listing(db, outlets, today())
    result: dict[str, list[OpenPiece]] = {}
    for outlet in outlets:
        counts = closed.get(outlet.id, [])
        first = firsts.get(outlet.id)
        if not counts or first is None:
            continue
        pieces: list[OpenPiece] = []
        cursor = first
        for start, end in counts:
            if cursor < start:
                pieces.extend(_split(cursor, start - timedelta(days=1), listed.get(outlet.id, []), OpenState.ABSORBED))
            cursor = max(cursor, end + timedelta(days=1))
        result[outlet.id] = list(reversed(pieces))
    return result


def open_pieces(db: Session, outlets: list[Outlet]) -> dict[str, list[OpenPiece]]:
    """Waktu yang belum ditutup per cabang, terbaru di atas: periode berjalan, periode yang harus ditutup, lalu bagian yang menjadi stok awalnya."""
    now = today()
    ids = [outlet.id for outlet in outlets]
    starts = running_starts(db, ids)
    last_ends = _last_ends(db, ids)
    listed = branch_periods.listing(db, outlets, now)
    result: dict[str, list[OpenPiece]] = {}
    for outlet in outlets:
        first = starts.get(outlet.id)
        if first is None:
            continue
        periods = listed.get(outlet.id, [])
        close_start, close_end = _closing_range(periods, last_ends.get(outlet.id), now, first if last_ends.get(outlet.id) is None else None)
        current = next((period for period in periods if period.start <= now <= period.end), None)
        pieces: list[OpenPiece] = []
        if close_end < now:
            running_start = close_end + timedelta(days=1)
            pieces.append(OpenPiece(running_start, None, OpenState.RUNNING, current.start if current else running_start, current.end if current else now))
            closing = next((period for period in periods if period.start <= close_end <= period.end), None)
            pieces.append(OpenPiece(close_start, close_end, OpenState.TO_CLOSE, closing.start if closing else close_start, closing.end if closing else close_end))
        else:
            pieces.append(OpenPiece(close_start, None, OpenState.RUNNING, current.start if current else close_start, current.end if current else now))
        if first < close_start:
            pieces.extend(reversed(_split(first, close_start - timedelta(days=1), periods, OpenState.OPENING)))
        result[outlet.id] = pieces
    return result


def record(db: Session, user: User, outlet_id: str, start: date, end: date, note: str | None, lines: list[BookedLine], source: str = SOURCE_WEB) -> IngredientCount:
    # Penutupan mengembalikan semua bahan ke 0, jadi minimal satu bahan wajib dihitung fisik supaya tidak tertutup karena salah tekan.
    if not lines:
        raise DomainError(messages.NO_COUNT)
    ensure_closable(db, outlet_id, start, end)
    ids = [line.ingredient_id for line in lines]
    if len(ids) != len(set(ids)):
        raise DomainError(messages.DUPLICATE_LINE)
    units = dict(db.execute(select(Ingredient.id, Ingredient.unit_id).where(Ingredient.id.in_(ids))).all()) if ids else {}

    count = IngredientCount(outlet_id=outlet_id, period_start=start, period_end=end, note=(note or "").strip() or None, user_id=user.id, source=source)
    db.add(count)
    # The lines and the adjustment cards both point at the count, and without a flush the order of the inserts is not guaranteed.
    db.flush()

    for line in lines:
        db.add(
            IngredientCountLine(
                count_id=count.id,
                ingredient_id=line.ingredient_id,
                ingredient_name=line.name,
                unit_id=units.get(line.ingredient_id),
                book_balance=line.book_balance,
                counted=line.counted,
                value=line.unit_price,
                shrink_tolerance=line.shrink_tolerance,
            )
        )
    _reset_to_zero(db, user, outlet_id, end, count, RESET_LABEL.format(start=start, end=end))
    count_requests.settle(db, user, outlet_id, count.id)
    count_drafts.discard(db, outlet_id)
    db.commit()
    return count


def ingredient_total(db: Session, outlet_id: str) -> int:
    """How many active ingredients the branch has: what the confirmation says will start the next period at 0."""
    return db.scalar(select(func.count()).select_from(Ingredient).where(Ingredient.outlet_id == outlet_id, Ingredient.is_active.is_(True))) or 0


def _reset_to_zero(db: Session, user: User, outlet_id: str, end: date, count: IngredientCount, note: str) -> None:
    """The balance at the end of the period, read under a lock on every ingredient row, is taken back to 0 by one card stamped a second before the period ends.

    The card carries the count, so the closed period's own report leaves it out and cancelling the count removes it.
    """
    names = dict(db.execute(select(Ingredient.id, Ingredient.name).where(Ingredient.outlet_id == outlet_id)).all())
    stock_balances.hold(db, names.keys(), [])
    balances = stock_balances.balances_before(db, outlet_id, end + timedelta(days=1))
    stamp = range_end(end) - timedelta(seconds=1)
    for ingredient_id, balance in balances.items():
        if balance == 0:
            continue
        db.add(
            IngredientCard(
                outlet_id=outlet_id,
                ingredient_id=ingredient_id,
                ingredient_name=names[ingredient_id],
                kind=INGREDIENT_ADJUSTMENT,
                qty=-balance,
                count_id=count.id,
                user_id=user.id,
                note=note,
                created_at=stamp,
            )
        )
