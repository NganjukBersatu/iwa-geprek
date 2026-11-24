"""Database reads of the summary."""
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.business_days import expenses_in, orders_in, valid_orders_in
from app.core.money import decimal_of
from app.models.expense import Expense, FundSource
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment_method import PaymentMethod
from web.management.reports.sales.summary.constants import TOP_ITEMS_LIMIT


def sales_totals(db: Session, start: date, end: date, outlet_id: str | None) -> tuple[int, int, Decimal, Decimal]:
    """Valid count, voided count, valid total, and valid cash total in one scan."""
    valid = Order.voided_at.is_(None)
    count, voided, total, cash = db.execute(
        select(
            func.count(case((valid, 1))),
            func.count(case((Order.voided_at.is_not(None), 1))),
            func.sum(case((valid, Order.total))),
            func.sum(case((valid & Order.is_cash(), Order.total))),
        ).where(*orders_in(start, end, outlet_id))
    ).one()
    return count or 0, voided or 0, decimal_of(total), decimal_of(cash)


def sales_by_method(db: Session, start: date, end: date, outlet_id: str | None) -> list[tuple]:
    """(master_id, payment code, count, total) of valid orders."""
    return list(
        db.execute(
            select(PaymentMethod.master_id, Order.payment_method, func.count(), func.sum(Order.total))
            .select_from(Order)
            .outerjoin(PaymentMethod, PaymentMethod.id == Order.payment_method_id)
            .where(*valid_orders_in(start, end, outlet_id))
            .group_by(PaymentMethod.master_id, Order.payment_method)
        ).all()
    )


def master_by_code(db: Session) -> dict[str, str]:
    """The first master id seen for each payment code, matching orders whose method was deleted."""
    masters: dict[str, str] = {}
    for code, master_id in db.execute(select(PaymentMethod.code, PaymentMethod.master_id)).all():
        if master_id:
            masters.setdefault(code, master_id)
    return masters


def top_items(db: Session, start: date, end: date, outlet_id: str | None) -> list[tuple]:
    """Grouped by the snapshot name, since a deleted menu item leaves its id empty."""
    return list(
        db.execute(
            select(
                func.max(OrderItem.menu_item_id),
                OrderItem.menu_item_name,
                func.sum(OrderItem.qty),
                func.sum(OrderItem.subtotal),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(*valid_orders_in(start, end, outlet_id))
            .group_by(OrderItem.menu_item_name)
            .order_by(func.sum(OrderItem.qty).desc())
            .limit(TOP_ITEMS_LIMIT)
        ).all()
    )


def bottom_items(db: Session, start: date, end: date, outlet_id: str | None) -> list[tuple]:
    """Least-selling items sold at all in the range, grouped by the snapshot name like `top_items`."""
    return list(
        db.execute(
            select(
                func.max(OrderItem.menu_item_id),
                OrderItem.menu_item_name,
                func.sum(OrderItem.qty),
                func.sum(OrderItem.subtotal),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(*valid_orders_in(start, end, outlet_id))
            .group_by(OrderItem.menu_item_name)
            .order_by(func.sum(OrderItem.qty).asc())
            .limit(TOP_ITEMS_LIMIT)
        ).all()
    )


def expense_totals(db: Session, start: date, end: date, outlet_id: str | None) -> tuple[Decimal, Decimal, int]:
    """Drawer-cash total, other-funds total, and count; an empty branch id means every branch here."""
    drawer, other, count = db.execute(
        select(
            func.sum(case((Expense.fund_source == FundSource.DRAWER_CASH, Expense.amount))),
            func.sum(case((Expense.fund_source == FundSource.OTHER_FUNDS, Expense.amount))),
            func.count(),
        ).where(*expenses_in(start, end, outlet_id))
    ).one()
    return decimal_of(drawer), decimal_of(other), count or 0


def expense_items(db: Session, start: date, end: date, outlet_id: str | None) -> list[tuple]:
    """Grouped by name, so off-catalogue purchases of the same thing still add up; largest first."""
    return list(
        db.execute(
            select(Expense.item_name, func.max(Expense.routine_item_id), func.count(), func.sum(Expense.amount))
            .where(*expenses_in(start, end, outlet_id))
            .group_by(Expense.item_name)
            .order_by(func.sum(Expense.amount).desc())
        ).all()
    )
