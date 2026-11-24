"""Overpayment of a non-cash method that takes any amount: kept in step with the order every time it changes."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.money import ZERO, decimal_of
from app.models.order import Order
from app.models.overpayment import Overpayment
from app.models.payment_method import PaymentMethod
from app.models.user import User

CASH_CODE = "tunai"
DELETED_ACCOUNT = "(akun dihapus)"


def sync(db: Session, order: Order, method: PaymentMethod | None) -> None:
    """Received minus total, only for non-cash methods that take any amount; zero or less removes the record."""
    extra = ZERO
    if method is not None and method.needs_change and method.code != CASH_CODE and order.cash_received is not None:
        extra = decimal_of(order.cash_received) - decimal_of(order.total)

    record = db.scalar(select(Overpayment).where(Overpayment.order_id == order.id))
    if extra <= 0:
        if record is not None:
            db.delete(record)
        return

    if record is None:
        cashier = db.get(User, order.cashier_id)
        record = Overpayment(
            id=str(uuid.uuid4()),
            order_id=order.id,
            outlet_id=order.outlet_id,
            cash_session_id=order.cash_session_id,
            cashier_id=order.cashier_id,
            cashier_name=cashier.username if cashier else DELETED_ACCOUNT,
        )
        db.add(record)
    assert method is not None
    record.method_code = method.code
    record.method_label = method.label
    record.order_total = decimal_of(order.total)
    record.received = decimal_of(order.cash_received)
    record.amount = extra
    record.recorded_at = order.created_at
