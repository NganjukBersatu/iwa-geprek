"""Every cash session with its reconciliation; the figures come from app.core.finance.session_totals."""
from datetime import date

from sqlalchemy.orm import Session

from app.core.branches import outlet_name
from app.core.errors import DomainError
from app.core.finance.session_rows import SessionHistoryRowOut, row_out, rows_of
from app.core.finance.session_totals import totals_of
from app.core.orders import reading as order_reading
from app.core.orders.order_schemas import order_out
from app.models.order import Order
from web.management.reports.common import month_to_date
from web.management.session_history import repository
from web.management.session_history.schemas import SessionHistoryPageOut, SessionOrderDetailOut

NOT_FOUND = 404
SESSION_NOT_FOUND = "Sesi tidak ditemukan."
ORDER_NOT_FOUND = "Transaksi tidak ditemukan."


def page(
    db: Session,
    start: date | None,
    end: date | None,
    outlet_id: str | None,
    running: bool | None,
    search: str | None,
    sort: str | None,
    number: int,
    size: int,
) -> SessionHistoryPageOut:
    start, end = month_to_date(start, end)
    found, total = repository.page_of(db, start, end, outlet_id, running, (search or "").strip() or None, sort, number, size)
    return SessionHistoryPageOut(
        start=start,
        end=end,
        items=rows_of(db, found),
        total=total,
        page=number,
        size=size,
    )


def detail(db: Session, session_id: str, outlet_id: str | None) -> SessionHistoryRowOut:
    found = repository.find_with_cashier(db, session_id)
    # Another branch's session answers as missing, so its existence is not revealed.
    if found is None or (outlet_id and found[0].outlet_id != outlet_id):
        raise DomainError(SESSION_NOT_FOUND, status=NOT_FOUND)
    session, username = found
    return row_out(session, username, outlet_name(db, session.outlet_id), totals_of(db, session.id))


def order_detail(db: Session, order_id: str, outlet_id: str | None) -> SessionOrderDetailOut:
    order = db.get(Order, order_id)
    # Another branch's order answers as missing, so its existence is not revealed.
    if order is None or (outlet_id and order.outlet_id != outlet_id):
        raise DomainError(ORDER_NOT_FOUND, status=NOT_FOUND)
    found = repository.find_with_cashier(db, order.cash_session_id)
    base = order_out(order_reading.lines_of(db, [order])[0])
    return SessionOrderDetailOut(**base.model_dump(), cashier_username=found[1] if found else None)
