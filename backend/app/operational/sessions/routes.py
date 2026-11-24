"""The till session of the person holding the tablet; the rules live in app.core.finance.session_control."""
from collections.abc import Iterator
from contextlib import contextmanager

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core import page_cursor
from app.core.orders.open_bills_visibility import show_open_bills
from app.core.auth import current_user, mark_used, require_permission
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.finance import session_control, session_totals
from app.core.finance.session_rows import rows_of
from app.core.orders import cancellations, session_page, stations
from app.core.orders import reading as order_reading
from app.core.orders.order_schemas import SessionOrderOut, StationOrderOut, StationOrderPageOut, order_out, station_order_out
from app.core.user_names import user_names
from app.models.cash_session import CashSession
from app.models.device import Device
from app.models.user import User
from app.operational.device import cashier_tablet
from app.operational.sessions import repository
from app.operational.sessions.schemas import MethodTotalOut, OwnSessionPageOut, RecapOut, SessionCloseIn, SessionOpenIn, SessionOut

router = APIRouter(prefix="/sessions", tags=["v2-operational-sessions"])
log = logging.getLogger("cafe.sessions")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _session_out(session: CashSession) -> SessionOut:
    return SessionOut(
        id=session.id,
        opened_at=session.opened_at,
        business_day=session.business_day,
        opening_cash=session.opening_cash,
        shift_code=session.shift_code,
        three_parts=session.planned_shopping is not None,
        planned_float=session.planned_float,
        planned_shopping=session.planned_shopping,
    )


def _recap_out(recap: session_control.Recap) -> RecapOut:
    session, totals = recap.session, recap.totals
    return RecapOut(
        session=_session_out(session),
        status=session.status,
        revenue=totals.revenue,
        cash_revenue=totals.cash_revenue,
        non_cash_revenue=totals.non_cash_revenue,
        drawer_expenses=totals.drawer_expenses,
        other_fund_expenses=totals.other_fund_expenses,
        shopping_fund_used=totals.shopping_fund_used,
        transactions=totals.transactions,
        voided_transactions=totals.voided_transactions,
        expected_cash=recap.expected_cash,
        expected_revenue=totals.expected_revenue,
        actual_cash=session.actual_cash,
        difference=session.difference,
        actual_float=session.actual_float,
        actual_shopping=session.actual_shopping,
        actual_revenue=session.actual_revenue,
        note=session.note,
    )


@router.get("/active", response_model=SessionOut | None)
def active(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Null when the person has no running session, which is a normal state, not an error."""
    session = session_control.active_of(db, user.id)
    return _session_out(session) if session else None


@router.get("/mine", response_model=OwnSessionPageOut)
def mine(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    sort: str | None = Query(None, pattern="^-?time$", description="time = oldest first, -time = newest first (the default)"),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Only the person's own sessions, whatever they may oversee; overseeing every session is the web history's job."""
    found, total = repository.own_page(db, user.id, start, end, page, size, sort)
    return OwnSessionPageOut(items=rows_of(db, found), total=total, page=page, size=size)


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def open_session(
    body: SessionOpenIn,
    device: Device = Depends(cashier_tablet),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(session_control.PERMISSION_OPEN)),
):
    """Only from a cashier tablet paired to a branch; the session belongs to that branch."""
    mark_used(db, device.id)
    with _domain_errors():
        session = session_control.open_session(db, user, device.outlet_id, body.opening_cash)
    shaped = _session_out(session)
    # Membuka sesi tidak boleh gagal karena pembersihan menu tertinggal; yang gagal dicoba lagi di pembukaan berikutnya.
    try:
        stations.close_stale(db, device.outlet_id, session.business_day)
        # Menu yatim yang lahir sebelum aturan ini ikut tertutup saat pertama kali sesi dibuka.
        stations.stop_orphans(db, device.outlet_id)
        db.commit()
    except Exception:
        db.rollback()
        log.exception("stale station tasks not closed", extra={"outlet_id": device.outlet_id})
    return shaped


@router.get("/{session_id}/recap", response_model=RecapOut)
def recap(session_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """The figures before closing, so the cashier knows what the drawer should hold before counting it."""
    with _domain_errors():
        session = session_control.owned(db, user, session_id)
    shaped = _recap_out(session_control.recap(db, session))
    shaped.station_open_orders = stations.open_count(db, session.id)
    return shaped


# Not cached: read while the session is still taking money, so it must be what the database holds now.
@router.get("/{session_id}/methods", response_model=list[MethodTotalOut])
def methods(session_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Revenue per payment method of the person's own session, largest first; two bank accounts show as two rows."""
    with _domain_errors():
        session = session_control.owned(db, user, session_id)
    return [MethodTotalOut(label=row.label, cash=row.cash, amount=row.amount, transactions=row.transactions) for row in session_totals.method_totals(db, session.id)]


@router.get("/{session_id}/orders", response_model=list[SessionOrderOut])
def orders(session_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Read only, oldest first; a void or correction is made from the web history."""
    with _domain_errors():
        session = session_control.owned(db, user, session_id)
    return [order_out(lines) for lines in order_reading.orders_of(db, session.id)]


# Tidak di-cache: daftar ini berubah di setiap penjualan dan pengajuan, dan tablet memuat ulang lewat sinyal /live.
@router.get("/{session_id}/orders/page", response_model=StationOrderPageOut, dependencies=[Depends(show_open_bills)])
def order_page(
    session_id: str,
    q: str | None = Query(None, max_length=session_page.MAX_QUERY_LENGTH),
    cursor: str | None = Query(None, max_length=page_cursor.MAX_CURSOR_LENGTH),
    limit: int = Query(page_cursor.DEFAULT_LIMIT, ge=1, le=page_cursor.MAX_LIMIT),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Terbaru dulu, berkursor; pencarian mencakup seluruh isi pesanan."""
    with _domain_errors():
        session = session_control.owned(db, user, session_id)
        found = session_page.page_of(db, session.id, q, cursor, limit)
    orders = [lines.order for lines in found.lines]
    latest = cancellations.latest_of_orders(db, [order.id for order in orders])
    names = user_names(db, [*(order.cashier_id for order in orders), *(request.requested_by_id for request in latest.values())])
    return StationOrderPageOut(
        orders=[station_order_out(lines, names, latest.get(lines.order.id)) for lines in found.lines],
        next_cursor=found.next_cursor,
    )


# Tidak di-cache: daftar ini berubah di setiap langkah stasiun, dan tablet memuat ulang lewat sinyal /live.
@router.get("/{session_id}/orders/left-behind", response_model=list[StationOrderOut])
def left_behind(session_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Pesanan dari sesi lain yang sudah ditutup di cabang sesi ini yang menunya masih di stasiun, terlama dulu."""
    with _domain_errors():
        session = session_control.owned(db, user, session_id)
    found = order_reading.lines_of(db, stations.left_behind_orders(db, session.outlet_id))
    latest = cancellations.latest_of_orders(db, [lines.order.id for lines in found])
    names = user_names(db, [*(lines.order.cashier_id for lines in found), *(request.requested_by_id for request in latest.values())])
    return [station_order_out(lines, names, latest.get(lines.order.id)) for lines in found]


@router.post("/{session_id}/close", response_model=RecapOut)
def close_session(
    session_id: str,
    body: SessionCloseIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(session_control.PERMISSION_OPEN)),
):
    """Not tied to a tablet, so a supervisor can close for a cashier who went home without closing."""
    closing = session_control.Closing(
        actual_cash=body.actual_cash,
        actual_float=body.actual_float,
        actual_shopping=body.actual_shopping,
        actual_revenue=body.actual_revenue,
        note=body.note,
    )
    with _domain_errors():
        result = session_control.close_session(db, user, session_id, closing)
    return _recap_out(result)
