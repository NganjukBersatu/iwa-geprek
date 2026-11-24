"""Requests to cancel an order, asked from the tablet and decided here; the rules live in app.core.orders.cancellations."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import readable_outlet_id, require_permission
from app.core.branches import branch_ids_in_scope, outlet_names
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.orders import cancellations
from app.core.user_names import user_names
from app.models.cancellation_request import CancellationRequest
from app.models.order import Order
from app.models.user import User
from web.management.cancellations.schemas import CancellationDecisionIn, CancellationOut, CancellationPageOut
from web.management.reports.menu import item_summary

router = APIRouter(prefix="/cancellations", tags=["v2-cancellations-manage"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@router.get("", response_model=CancellationPageOut)
def list_waiting(
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(cancellations.PERMISSION_DECIDE)),
):
    """Waiting requests, oldest first, in a fixed number of queries whatever the page holds; never cached, the screen reloads on live signals."""
    found = cancellations.pending_page(db, branch_ids_in_scope(db, outlet_id), page, size)
    return CancellationPageOut(items=_out(db, found.requests), total=found.total, page=page, size=size)


@router.post("/{request_id}/decision", status_code=status.HTTP_204_NO_CONTENT)
def decide(
    request_id: str,
    body: CancellationDecisionIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(cancellations.PERMISSION_DECIDE)),
):
    try:
        cancellations.decide(db, user, user.locked_outlet_id, request_id, body.approve, body.note)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _out(db: Session, requests: list[CancellationRequest]) -> list[CancellationOut]:
    order_ids = [row.order_id for row in requests]
    orders = {order.id: order for order in db.scalars(select(Order).where(Order.id.in_(order_ids))).all()} if order_ids else {}
    names = user_names(db, [row.requested_by_id for row in requests] + [order.cashier_id for order in orders.values()])
    branches = outlet_names(db, (row.outlet_id for row in requests))
    texts = item_summary.summaries(db, order_ids)
    return [
        CancellationOut(
            id=row.id,
            outlet_id=row.outlet_id,
            outlet_name=branches.get(row.outlet_id, ""),
            order_id=row.order_id,
            receipt_number=order.receipt_number,
            customer_name=order.customer_name,
            table_no=order.table_no,
            order_total=order.total,
            order_created_at=order.created_at,
            order_business_day=order.business_day,
            items_summary=texts.get(row.order_id, ""),
            cashier=names.get(order.cashier_id, ""),
            requested_by=names.get(row.requested_by_id, ""),
            reason=row.reason,
            created_at=row.created_at,
        )
        for row in requests
        if (order := orders.get(row.order_id)) is not None
    ]
