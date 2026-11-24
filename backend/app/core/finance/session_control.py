"""Opening, reviewing and closing a cashier's till session; every figure comes from app.core.finance.session_totals."""
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import WIB, local_date, now, today
from app.core.errors import DomainError
from app.core.finance.session_totals import SessionTotals, expected_cash, totals_of
from app.core.money import ZERO, decimal_of
from app.core.orders.open_bills_visibility import INCLUDE_OPTION
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.order import Order
from app.models.outlet import Outlet
from app.models.schedule import Schedule
from app.models.user import User

PERMISSION_OPEN = "shift.buka"
PERMISSION_VIEW_ALL = "shift.lihat_semua"

FORBIDDEN = 403
NOT_FOUND = 404
MINUTES_PER_DAY = 24 * 60

STILL_OPEN = "Masih ada sesi yang belum ditutup. Tutup sesi itu dulu sebelum membuka sesi baru."
SESSION_NOT_FOUND = "Sesi tidak ditemukan."
SESSION_OF_OTHER = "Sesi ini milik kasir lain."
ALREADY_CLOSED = "Sesi ini sudah ditutup."
NEEDS_THREE_PARTS = "Isi ketiga bagian uang: uang modal, uang belanja, dan uang omzet."
NEEDS_ACTUAL_CASH = "Isi uang aktual di laci."
NEEDS_INTERVENTION_NOTE = "Isi alasan menutup sesi kasir lain."
OPEN_BILLS_BLOCK_CLOSING = "Masih ada {count} bill yang belum dibayar. Bayar atau batalkan dulu sebelum sesi ditutup."
CONFLICT = 409


@dataclass(frozen=True)
class Recap:
    session: CashSession
    totals: SessionTotals
    expected_cash: Decimal

    @property
    def three_parts(self) -> bool:
        """Decided when the session opened, from the plots copied onto it, not by today's branch settings."""
        return self.session.planned_shopping is not None


@dataclass(frozen=True)
class Closing:
    """One counted figure, or the three parts when the session holds a shopping fund."""

    actual_cash: Decimal | None
    actual_float: Decimal | None
    actual_shopping: Decimal | None
    actual_revenue: Decimal | None
    note: str | None


def active_of(db: Session, user_id: str) -> CashSession | None:
    return db.scalar(select(CashSession).where(CashSession.cashier_id == user_id, CashSession.status == CashSessionStatus.OPEN))


def held(db: Session, session_id: str) -> CashSession | None:
    """Reads a session again under a shared lock kept until the caller commits: a close waits for a sale or expense being written into it, and the writer sees the status that close left."""
    return db.scalar(select(CashSession).where(CashSession.id == session_id).with_for_update(read=True).execution_options(populate_existing=True))


def running_of(db: Session, user_id: str) -> CashSession | None:
    """The cashier's running session held as in held(), or none once a close got there first."""
    found = active_of(db, user_id)
    session = held(db, found.id) if found is not None else None
    return session if session is not None and session.status == CashSessionStatus.OPEN else None


def business_day_of(db: Session, user_id: str) -> date:
    """The business day a person works in now: their running session's, or today when none runs."""
    session = active_of(db, user_id)
    return session.business_day if session is not None else today()


def _minutes(clock: str | None) -> int:
    if not clock:
        return 0
    hours, _, minutes = clock.partition(":")
    try:
        return int(hours) * 60 + int(minutes or 0)
    except ValueError:
        return 0


def _schedule_for(db: Session, user_id: str, at: datetime) -> Schedule | None:
    """Today's row whose start is closest to now, around the clock, for a person with two assignments in a day."""
    rows = db.scalars(select(Schedule).where(Schedule.user_id == user_id, Schedule.date == local_date(at))).all()
    if not rows:
        return None
    local = at.astimezone(WIB)
    current = local.hour * 60 + local.minute

    def distance(row: Schedule) -> int:
        gap = abs(current - _minutes(row.shift_code.start_clock if row.shift_code else None))
        return min(gap, MINUTES_PER_DAY - gap)

    return min(rows, key=distance)


def open_session(db: Session, user: User, outlet_id: str, opening_cash: Decimal) -> CashSession:
    # The person's row is locked first, so a double tap opens one session and the second sees it.
    db.execute(select(User.id).where(User.id == user.id).with_for_update())
    if active_of(db, user.id) is not None:
        raise DomainError(STILL_OPEN)
    started = now()
    schedule = _schedule_for(db, user.id, started)
    code = schedule.shift_code if schedule else None
    # The branch plots are copied, so a running session never changes when the amounts change later.
    outlet = db.get(Outlet, outlet_id)
    planned_shopping = outlet.spending_float if outlet else None
    planned_float = None
    if planned_shopping is not None and outlet is not None:
        planned_float = outlet.cash_float if outlet.cash_float is not None else opening_cash
    session = CashSession(
        id=str(uuid.uuid4()),
        outlet_id=outlet_id,
        cashier_id=user.id,
        shift_code_id=code.id if code else None,
        shift_code=code.code if code else None,
        shift_code_color=code.color if code else None,
        opened_at=started,
        opening_cash=opening_cash,
        system_revenue=ZERO,
        cash_revenue=ZERO,
        drawer_expenses=ZERO,
        planned_float=planned_float,
        planned_shopping=planned_shopping,
        status=CashSessionStatus.OPEN,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def owned(db: Session, user: User, session_id: str) -> CashSession:
    """One's own session, or anyone's for those who oversee every session, so a cashier who went home can be closed for."""
    session = db.get(CashSession, session_id)
    if session is None:
        raise DomainError(SESSION_NOT_FOUND, status=NOT_FOUND)
    if session.cashier_id != user.id and not user.allows(PERMISSION_VIEW_ALL):
        raise DomainError(SESSION_OF_OTHER, status=FORBIDDEN)
    return session


def recap(db: Session, session: CashSession) -> Recap:
    totals = totals_of(db, session.id)
    return Recap(session=session, totals=totals, expected_cash=expected_cash(session, totals))


def open_bill_count(db: Session, session_id: str) -> int:
    """Bills written but not yet paid; written with the literal is_open condition so the partial index serves it."""
    statement = select(func.count()).select_from(Order).where(Order.cash_session_id == session_id, Order.is_open.is_(True))
    return db.scalar(statement.execution_options(**{INCLUDE_OPTION: True})) or 0


def close_session(db: Session, user: User, session_id: str, closing: Closing) -> Recap:
    session = owned(db, user, session_id)
    # Waits for sales and expenses still being written into it, so the frozen figures include them and nothing lands after.
    db.refresh(session, with_for_update=True)
    if session.status == CashSessionStatus.CLOSED:
        raise DomainError(ALREADY_CLOSED)
    unpaid = open_bill_count(db, session.id)
    if unpaid:
        raise DomainError(OPEN_BILLS_BLOCK_CLOSING.format(count=unpaid), status=CONFLICT)
    # Closing someone else's session is an intervention, so it always leaves its reason on the session.
    if session.cashier_id != user.id and not (closing.note or "").strip():
        raise DomainError(NEEDS_INTERVENTION_NOTE)
    current = recap(db, session)
    totals = current.totals
    session.system_revenue = totals.revenue
    session.cash_revenue = totals.cash_revenue
    session.drawer_expenses = totals.drawer_expenses
    if current.three_parts:
        if closing.actual_float is None or closing.actual_shopping is None or closing.actual_revenue is None:
            raise DomainError(NEEDS_THREE_PARTS)
        session.actual_float = closing.actual_float
        session.actual_shopping = closing.actual_shopping
        session.actual_revenue = closing.actual_revenue
        # One equivalent figure, so actual minus expected still equals the sum of the three parts' differences.
        session.actual_cash = (
            closing.actual_float + closing.actual_revenue + totals.shopping_fund_used + (closing.actual_shopping - decimal_of(session.planned_shopping))
        )
    else:
        if closing.actual_cash is None:
            raise DomainError(NEEDS_ACTUAL_CASH)
        session.actual_cash = closing.actual_cash
    session.note = (closing.note or "").strip() or None
    session.difference = session.actual_cash - current.expected_cash
    session.closed_at = now()
    session.status = CashSessionStatus.CLOSED
    db.commit()
    db.refresh(session)
    return Recap(session=session, totals=totals, expected_cash=current.expected_cash)
