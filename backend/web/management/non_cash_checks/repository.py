"""Database reads and writes of the non-cash checks."""
from datetime import date

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.business_days import valid_orders_in
from app.core.money import decimal_of
from app.models.order import Order
from web.management.non_cash_checks.model import NonCashCheck


def recorded_by_outlet(db: Session, outlet_ids: list[str], start: date, end: date) -> dict[str, dict[date, Decimal]]:
    """Per branch and business day, the money that really reached the account (overpayment included, not the order total) of non-voided non-cash orders: one grouped query."""
    day = Order.business_day
    recorded: dict[str, dict[date, Decimal]] = {outlet_id: {} for outlet_id in outlet_ids}
    rows = db.execute(
        select(Order.outlet_id, day, func.sum(func.coalesce(Order.cash_received, Order.total)))
        .where(
            *valid_orders_in(start, end, None),
            Order.outlet_id.in_(outlet_ids),
            Order.payment_method.is_not(None),
            ~Order.is_cash(),
        )
        .group_by(Order.outlet_id, day)
    ).all()
    for outlet_id, row_day, total in rows:
        recorded[outlet_id][row_day] = decimal_of(total)
    return recorded


def checks_by_outlet(db: Session, outlet_ids: list[str], start: date, end: date) -> dict[str, dict[date, NonCashCheck]]:
    """The bank figures typed for the branches asked for, in one query."""
    found: dict[str, dict[date, NonCashCheck]] = {outlet_id: {} for outlet_id in outlet_ids}
    for row in db.scalars(select(NonCashCheck).where(NonCashCheck.outlet_id.in_(outlet_ids), NonCashCheck.date >= start, NonCashCheck.date <= end)):
        found[row.outlet_id][row.date] = row
    return found


def find(db: Session, outlet_id: str, day: date) -> NonCashCheck | None:
    return db.scalar(select(NonCashCheck).where(NonCashCheck.outlet_id == outlet_id, NonCashCheck.date == day))
