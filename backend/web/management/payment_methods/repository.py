"""Database reads for the payment method screen."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.payment_method import PaymentMethod


def find(db: Session, method_id: str) -> PaymentMethod | None:
    return db.get(PaymentMethod, method_id)


def with_code(db: Session, outlet_id: str, code: str) -> PaymentMethod | None:
    return db.scalar(select(PaymentMethod).where(PaymentMethod.outlet_id == outlet_id, PaymentMethod.code == code))


def other_active_count(db: Session, outlet_id: str, method_id: str) -> int:
    return db.scalar(
        select(func.count(PaymentMethod.id)).where(
            PaymentMethod.outlet_id == outlet_id, PaymentMethod.is_active.is_(True), PaymentMethod.id != method_id
        )
    ) or 0


def usage(db: Session, outlet_id: str | None) -> dict[tuple[str, str], int]:
    """Orders per (branch, method code); one branch, or every branch when none is given."""
    query = select(Order.outlet_id, Order.payment_method, func.count(Order.id)).where(Order.payment_method.is_not(None))
    if outlet_id is not None:
        query = query.where(Order.outlet_id == outlet_id)
    rows = db.execute(query.group_by(Order.outlet_id, Order.payment_method)).all()
    return {(branch, code): count for branch, code, count in rows}
