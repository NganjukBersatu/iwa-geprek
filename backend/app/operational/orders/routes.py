"""Sales from the till; the rules live in app.core.orders.create."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_permission
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.finance import session_control
from app.core.orders import create, open_bills, receipt_numbers, reading
from app.core.orders.order_schemas import order_out
from app.core.orders.lines import LineInput
from app.core.orders.options import ExtraPick
from app.models.device import Device
from app.models.order import Order
from app.core.user_names import user_names
from app.models.user import User
from app.operational.device import cashier_tablet
from app.operational.orders.schemas import BillCancelIn, BillLinesIn, BillQuoteIn, BillQuoteOut, BillSettleIn, OpenBillOut, OrderIn, OrderLineIn, OrderOut, ReceiptNumberOut

router = APIRouter(prefix="/orders", tags=["v2-operational-orders"])


def _out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        receipt_number=order.receipt_number,
        total=order.total,
        cash_received=order.cash_received,
        payment_method_label=order.payment_method_label,
        created_at=order.created_at,
    )


@router.post("/receipt-number", response_model=ReceiptNumberOut)
def take_receipt_number(
    _device: Device = Depends(cashier_tablet),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(create.PERMISSION)),
):
    """Taken before payment so the kitchen ticket and the receipt match; needs a running session so no number is burnt without a sale."""
    session = session_control.active_of(db, user.id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=create.NO_OPEN_SESSION)
    return ReceiptNumberOut(receipt_number=receipt_numbers.take(db, session.outlet_id, session.business_day))


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    body: OrderIn,
    _device: Device = Depends(cashier_tablet),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(create.PERMISSION)),
):
    """Sending the same client_id again returns the first order, so a queue that resends never sells twice."""
    sale = create.NewOrder(
        client_id=body.client_id,
        session_id=body.session_id,
        order_type=body.order_type,
        customer_name=body.customer_name,
        table_no=body.table_no,
        payment_method=body.payment_method or "",
        cash_received=body.cash_received,
        receipt_number=body.receipt_number,
        created_at=body.created_at,
        visitor_category_id=body.visitor_category_id,
        visitor_gender_id=body.visitor_gender_id,
        customer_id=body.customer_id,
        note_id=body.note_id,
        note_label=body.note_label,
        promo_id=body.promo_id,
        open_bill=body.open_bill,
        lines=[
            LineInput(
                menu_item_id=line.menu_item_id,
                qty=line.qty,
                note=line.note,
                variant_ids=line.variant_ids,
                extras=[ExtraPick(extra_id=pick.extra_id, qty=pick.qty) for pick in line.extras],
            )
            for line in body.items
        ],
    )
    try:
        order = create.record(db, user, sale)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return _out(order)


def _lines(items: list[OrderLineIn]) -> list[LineInput]:
    return [
        LineInput(
            menu_item_id=line.menu_item_id,
            qty=line.qty,
            note=line.note,
            variant_ids=line.variant_ids,
            extras=[ExtraPick(extra_id=pick.extra_id, qty=pick.qty) for pick in line.extras],
        )
        for line in items
    ]


def _bill_out(db: Session, order: Order, user: User) -> OpenBillOut:
    return _bills_out(db, [order], user)[0]


def _bills_out(db: Session, orders: list[Order], user: User) -> list[OpenBillOut]:
    names = user_names(db, [order.cashier_id for order in orders])
    return [
        OpenBillOut(**order_out(lines).model_dump(), cashier_name=names.get(lines.order.cashier_id), mine=lines.order.cashier_id == user.id)
        for lines in reading.lines_of(db, orders)
    ]


@router.get("/open", response_model=list[OpenBillOut])
def list_open_bills(
    device: Device = Depends(cashier_tablet),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(create.PERMISSION)),
):
    """Every unpaid bill of the branch, so a cashier taking over a shift sees what is still owed; never cached, it changes with every order."""
    return _bills_out(db, open_bills.of_outlet(db, device.outlet_id), user)


@router.post("/{order_id}/lines", response_model=OpenBillOut)
def add_bill_lines(
    order_id: str,
    body: BillLinesIn,
    device: Device = Depends(cashier_tablet),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(create.PERMISSION)),
):
    try:
        order = open_bills.add_lines(db, user, order_id, device.outlet_id, body.version, _lines(body.items))
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return _bill_out(db, order, user)


@router.post("/{order_id}/settle", response_model=OpenBillOut)
def settle_bill(
    order_id: str,
    body: BillSettleIn,
    device: Device = Depends(cashier_tablet),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(create.PERMISSION)),
):
    payment = open_bills.Settlement(payment_method=body.payment_method, cash_received=body.cash_received, promo_id=body.promo_id, settle_key=body.settle_key)
    try:
        order = open_bills.settle(db, user, order_id, device.outlet_id, body.version, payment)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return _bill_out(db, order, user)


@router.post("/{order_id}/quote", response_model=BillQuoteOut)
def quote_bill(
    order_id: str,
    body: BillQuoteIn,
    device: Device = Depends(cashier_tablet),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(create.PERMISSION)),
):
    """The price of the bill with the promo the cashier is looking at; read-only."""
    try:
        found = open_bills.quote(db, user, order_id, device.outlet_id, body.promo_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return BillQuoteOut(subtotal=found.subtotal, discount=found.discount, total=found.total, promo_name=found.promo_name)


@router.post("/{order_id}/cancel", response_model=OpenBillOut)
def cancel_bill(
    order_id: str,
    body: BillCancelIn,
    device: Device = Depends(cashier_tablet),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(create.PERMISSION)),
):
    try:
        order = open_bills.cancel(db, user, order_id, device.outlet_id, body.reason)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return _bill_out(db, order, user)
