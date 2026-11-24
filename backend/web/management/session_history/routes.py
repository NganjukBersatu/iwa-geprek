"""HTTP surface of the cash session history: reading, corrections, and closing a running session as an intervention."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import current_user, readable_outlet_id, require_permission
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.core.finance import session_control, sessions
from app.core.finance.session_rows import SessionHistoryRowOut
from app.core.orders import open_bills
from app.core.orders import edit as order_edit
from app.core.orders import lines as order_lines
from app.core.orders import options as order_options
from app.core.orders import reading as order_reading
from app.core.orders.order_schemas import SESSION_ORDER_SORTING, SessionOrderOut, order_out
from app.models.user import User
from web.management.session_history import catalog, service
from web.management.session_history.schemas import (
    OrderEditIn,
    OrderVoidIn,
    SessionInterventionIn,
    SessionClosingOut,
    SessionCorrectionIn,
    SessionHistoryPageOut,
    SessionImpactOut,
    SessionOrderDetailOut,
    OrderCatalogOut,
)

router = APIRouter(prefix="/session-history", tags=["web-session-history"])

PERMISSION_VIEW_ALL = "shift.lihat_semua"
PERMISSION_VOID = "order.void"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_SEARCH_LENGTH = 100

PAGE = TypeAdapter(SessionHistoryPageOut)
ORDERS = TypeAdapter(list[SessionOrderOut])
ROW = TypeAdapter(SessionHistoryRowOut)


@router.get("", response_model=SessionHistoryPageOut)
def list_sessions(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    running: bool | None = Query(None, description="True for running sessions, false for closed ones, empty for both"),
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the cashier name, shift code, or note"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW_ALL)),
):
    try:
        # Free text has no end of values, so it is never a key.
        if (search or "").strip():
            return service.page(db, start, end, outlet_id, running, search, sort, page, size)
        return cache.read(
            "web.session-history",
            (start, end, outlet_id, running, sort, page, size),
            lambda: service.page(db, start, end, outlet_id, running, None, sort, page, size),
            PAGE,
            cache.LIST_SECONDS,
        )
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.patch("/{session_id}", response_model=SessionHistoryRowOut)
def correct_session(
    session_id: str,
    body: SessionCorrectionIn,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Correction rights are checked in app.core.finance.sessions: all sessions, or one's own while it runs."""
    try:
        sessions.correct(
            db, user, session_id, outlet_id, body.opening_cash, body.actual_cash, body.note, "note" in body.model_fields_set
        )
        return service.detail(db, session_id, outlet_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.get("/{session_id}/closing", response_model=SessionClosingOut)
def closing_figures(
    session_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_VIEW_ALL)),
):
    """Never cached: the figures are read just before money is counted against them."""
    try:
        service.detail(db, session_id, outlet_id)
        figures = session_control.recap(db, session_control.owned(db, user, session_id))
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    session = figures.session
    return SessionClosingOut(
        three_parts=figures.three_parts,
        expected_cash=figures.expected_cash,
        planned_float=session.planned_float,
        planned_shopping=session.planned_shopping,
        expected_revenue=figures.totals.expected_revenue,
    )


@router.post("/{session_id}/close", response_model=SessionHistoryRowOut)
def close_session(
    session_id: str,
    body: SessionInterventionIn,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_VIEW_ALL)),
):
    """The intervention path for a cashier who cannot close from the tablet; the rules are the tablet's own, in app.core.finance.session_control."""
    closing = session_control.Closing(
        actual_cash=body.actual_cash,
        actual_float=body.actual_float,
        actual_shopping=body.actual_shopping,
        actual_revenue=body.actual_revenue,
        note=body.note,
    )
    try:
        service.detail(db, session_id, outlet_id)
        session_control.close_session(db, user, session_id, closing)
        return service.detail(db, session_id, outlet_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.get("/{session_id}/impact", response_model=SessionImpactOut)
def deletion_impact(
    session_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """What a delete would take, so the prompt states real numbers."""
    try:
        found = sessions.impact(db, user, session_id, outlet_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return SessionImpactOut(orders=found.orders, expenses=found.expenses)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    try:
        sessions.delete_session(db, user, session_id, outlet_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{session_id}/orders", response_model=list[SessionOrderOut])
def session_orders(
    session_id: str,
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW_ALL)),
):
    def build() -> list[SessionOrderOut]:
        service.detail(db, session_id, outlet_id)
        return SESSION_ORDER_SORTING.apply([order_out(lines) for lines in order_reading.orders_of(db, session_id)], sort)

    try:
        return cache.read("web.session-history.orders", (session_id, outlet_id, sort), build, ORDERS, cache.LIST_SECONDS)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


# Tidak di-cache: bill belum dibayar berubah di setiap pesanan dan pembayaran.
@router.get("/{session_id}/open-bills", response_model=list[SessionOrderOut])
def session_open_bills(
    session_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW_ALL)),
):
    """Bill yang sudah diterima dapur tetapi belum dibayar; belum masuk omzet sesi sampai dibayar."""
    try:
        service.detail(db, session_id, outlet_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return [order_out(lines) for lines in order_reading.lines_of(db, open_bills.of_session(db, session_id))]


@router.get("/orders/{order_id}", response_model=SessionOrderDetailOut)
def order_detail(
    order_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW_ALL)),
):
    """One transaction with its lines, for the page of a single transaction."""
    try:
        return service.order_detail(db, order_id, outlet_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Deleting an order returns its ingredients and stock; a closed session's figures are worked out again."""
    try:
        sessions.delete_order(db, user, order_id, outlet_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/orders/{order_id}/void", response_model=SessionOrderOut)
def void_order(
    order_id: str,
    body: OrderVoidIn,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_VOID)),
):
    """Cancels a transaction at once: it stays on record as cancelled, its stock and ingredients come back."""
    try:
        order = sessions.void_order(db, user, order_id, outlet_id, body.reason)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return order_out(order_reading.lines_of(db, [order])[0])


@router.get("/orders/{order_id}/catalog", response_model=OrderCatalogOut)
def order_catalog(
    order_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW_ALL)),
):
    """Menus, promos and payment methods of the order's own branch, for the correction dialog."""
    try:
        return catalog.of_order(db, order_id, outlet_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.patch("/orders/{order_id}", response_model=SessionOrderOut)
def correct_order(
    order_id: str,
    body: OrderEditIn,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Corrects the content of a transaction; its number and time stay, stock and totals are worked out again."""
    change = order_edit.OrderChange(
        customer_name=body.customer_name,
        table_no=body.table_no,
        order_type=body.order_type,
        payment_method=body.payment_method,
        cash_received=body.cash_received,
        lines=None
        if body.lines is None
        else [
            order_lines.LineInput(
                menu_item_id=line.menu_item_id,
                qty=line.qty,
                note=line.note,
                variant_ids=line.variant_ids,
                extras=[order_options.ExtraPick(extra_id=pick.extra_id, qty=pick.qty) for pick in line.extras],
            )
            for line in body.lines
        ],
        promo_id=body.promo_id,
        remove_promo=body.remove_promo,
    )
    try:
        order = order_edit.edit_order(db, user, order_id, outlet_id, change)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return order_out(order_reading.lines_of(db, [order])[0])


@router.get("/{session_id}", response_model=SessionHistoryRowOut)
def session_detail(
    session_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW_ALL)),
):
    try:
        return cache.read(
            "web.session-history.detail",
            (session_id, outlet_id),
            lambda: service.detail(db, session_id, outlet_id),
            ROW,
            cache.LIST_SECONDS,
        )
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
