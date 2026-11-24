"""Database reads of the transaction list."""
from sqlalchemy import case, func, not_, select
from sqlalchemy.orm import Session

from app.models.order import CASH_METHOD, Order
from app.core.sorting import SqlSorting
from app.models.user import User

# Orders without a method predate the column and count as cash.
effective_method = func.coalesce(Order.payment_method, CASH_METHOD)


def method_totals(db: Session, window: tuple) -> list[tuple]:
    return db.execute(
        select(effective_method, func.max(Order.payment_method_label), func.count(), func.sum(Order.total))
        .where(*window, Order.voided_at.is_(None))
        .group_by(effective_method)
        .order_by(func.sum(Order.total).desc())
    ).all()


def transaction_conditions(window: tuple, group: str, method: str | None, include_voided: bool) -> list:
    conditions = list(window)
    if not include_voided:
        conditions.append(Order.voided_at.is_(None))
    if group == "cash":
        conditions.append(Order.is_cash())
    elif group == "non_cash":
        conditions.append(not_(Order.is_cash()))
    if method:
        conditions.append(effective_method == method)
    return conditions


def transaction_count_and_amount(db: Session, conditions: list) -> tuple:
    """Voided orders are counted but never add to the amount."""
    return db.execute(
        select(func.count(), func.coalesce(func.sum(case((Order.voided_at.is_(None), Order.total), else_=0)), 0))
        .where(*conditions)
    ).one()


SORTING = SqlSorting(
    columns={
        "created_at": Order.created_at,
        "receipt": Order.receipt_number,
        "cashier": select(User.username).where(User.id == Order.cashier_id).scalar_subquery(),
        "place": func.coalesce(func.nullif(Order.table_no, ""), func.nullif(Order.customer_name, "")),
        "method": Order.payment_method_label,
        "voided": Order.voided_at.is_not(None),
        "total": Order.total,
    },
    default=(Order.created_at.desc(),),
    tiebreak=Order.id,
)


def transaction_page(db: Session, conditions: list, sort: str | None, page: int, per_page: int) -> list[Order]:
    return list(
        db.scalars(
            select(Order)
            .where(*conditions)
            .order_by(*SORTING.order_by(sort))
            .offset((page - 1) * per_page)
            .limit(per_page)
        ).all()
    )
