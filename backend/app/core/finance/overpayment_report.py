"""Non-cash overpayments, newest first, with what each order bought; the web report and the tablet both read it."""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.branches import outlet_names
from app.core.business_days import overpayments_in
from app.core.money import decimal_of
from app.core.sorting import SqlSorting
from app.models.outlet import Outlet
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.overpayment import Overpayment

# A purchase summary names at most this many lines before collapsing the rest into a count.
SUMMARY_LINES = 6
MORE_ITEMS = " +{count} lainnya"


class OverpaymentOut(BaseModel):
    id: str
    order_id: str
    outlet_id: str
    outlet_name: str
    # The cash session the order belongs to now, where it is corrected; empty for an order without one.
    session_id: str | None
    receipt_number: str | None
    recorded_at: datetime
    cashier: str
    method_label: str
    order_total: Decimal
    received: Decimal
    amount: Decimal
    voided: bool
    item_count: int
    purchases: str


class OverpaymentsOut(BaseModel):
    start: date
    end: date
    count: int
    total_amount: Decimal
    page: int
    per_page: int
    rows: list[OverpaymentOut]


def purchase_summary(items: list[tuple[int, str]]) -> str:
    lines = [f"{qty}x {name}" for qty, name in items]
    text = ", ".join(lines[:SUMMARY_LINES])
    return text + (MORE_ITEMS.format(count=len(lines) - SUMMARY_LINES) if len(lines) > SUMMARY_LINES else "")


SORTING = SqlSorting(
    columns={
        "receipt": Order.receipt_number,
        "outlet": select(Outlet.name).where(Outlet.id == Overpayment.outlet_id).scalar_subquery(),
        "business_day": Overpayment.business_day,
        "recorded_at": Overpayment.recorded_at,
        "cashier": Overpayment.cashier_name,
        "method": Overpayment.method_label,
        "voided": Order.voided_at.is_not(None),
        "order_total": Overpayment.order_total,
        "received": Overpayment.received,
        "amount": Overpayment.amount,
    },
    default=(Overpayment.business_day.desc(), Overpayment.recorded_at.desc()),
    tiebreak=Overpayment.id,
)


def report(
    db: Session,
    start: date,
    end: date,
    outlet_id: str | None,
    cashier_id: str | None,
    method: str | None,
    sort: str | None,
    page: int,
    per_page: int,
) -> OverpaymentsOut:
    """The total includes overpayments of orders voided later, since that money already reached the account."""
    conditions = [*overpayments_in(start, end, outlet_id)]
    if cashier_id:
        conditions.append(Overpayment.cashier_id == cashier_id)
    if method:
        conditions.append(Overpayment.method_code == method)
    count, total = db.execute(select(func.count(), func.coalesce(func.sum(Overpayment.amount), 0)).where(*conditions)).one()
    rows = db.execute(
        select(Overpayment, Order.receipt_number, Order.voided_at, Order.cash_session_id)
        .join(Order, Order.id == Overpayment.order_id)
        .where(*conditions)
        .order_by(*SORTING.order_by(sort))
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()
    items = _items_by_order(db, [record.order_id for record, _, _, _ in rows])
    names = outlet_names(db, [record.outlet_id for record, _, _, _ in rows])
    return OverpaymentsOut(
        start=start,
        end=end,
        count=int(count),
        total_amount=decimal_of(total),
        page=page,
        per_page=per_page,
        rows=[
            _row(record, names.get(record.outlet_id, ""), session_id, receipt_number, voided_at is not None, items.get(record.order_id, []))
            for record, receipt_number, voided_at, session_id in rows
        ],
    )


def _row(record: Overpayment, branch_name: str, session_id: str | None, receipt_number: str | None, voided: bool, items: list[tuple[int, str]]) -> OverpaymentOut:
    return OverpaymentOut(
        id=record.id,
        order_id=record.order_id,
        outlet_id=record.outlet_id,
        outlet_name=branch_name,
        session_id=session_id,
        receipt_number=receipt_number,
        recorded_at=record.recorded_at,
        cashier=record.cashier_name,
        method_label=record.method_label,
        order_total=record.order_total,
        received=record.received,
        amount=record.amount,
        voided=voided,
        item_count=len(items),
        purchases=purchase_summary(items),
    )


def _items_by_order(db: Session, order_ids: list[str]) -> dict[str, list[tuple[int, str]]]:
    items: dict[str, list[tuple[int, str]]] = {}
    if not order_ids:
        return items
    for order_id, qty, name in db.execute(
        select(OrderItem.order_id, OrderItem.qty, OrderItem.menu_item_name).where(OrderItem.order_id.in_(order_ids)).order_by(OrderItem.order_id)
    ).all():
        items.setdefault(order_id, []).append((qty, name))
    return items
