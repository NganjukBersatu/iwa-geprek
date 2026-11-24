"""Database reads of the voids report."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.business_days import orders_in
from app.models.order import Order
from app.core.sorting import SqlSorting
from app.models.user import User


def voided_between(start: date, end: date, outlet_id: str | None) -> tuple:
    """Voided orders of the business days in the range, the days their sale and its reversal both belong to."""
    return (*orders_in(start, end, outlet_id), Order.voided_at.is_not(None))


def void_totals(db: Session, conditions: tuple) -> tuple:
    """Number and total value of the voided orders."""
    return db.execute(
        select(func.count(), func.coalesce(func.sum(Order.total), 0)).select_from(Order).where(*conditions)
    ).one()


def voids_by_user(db: Session, conditions: tuple) -> list:
    """(voided_by id, count, total) per voider."""
    return db.execute(
        select(Order.voided_by_id, func.count(), func.coalesce(func.sum(Order.total), 0))
        .where(*conditions)
        .group_by(Order.voided_by_id)
    ).all()


SORTING = SqlSorting(
    columns={
        "order": func.coalesce(func.nullif(Order.customer_name, ""), ""),
        "reason": Order.void_reason,
        "voided_at": Order.voided_at,
        "created_at": Order.created_at,
        "cashier": select(User.username).where(User.id == Order.cashier_id).scalar_subquery(),
        "voided_by": select(User.username).where(User.id == Order.voided_by_id).scalar_subquery(),
        "total": Order.total,
    },
    default=(Order.voided_at.desc(),),
    tiebreak=Order.id,
)


def voided_page(db: Session, conditions: tuple, sort: str | None, page: int, per_page: int) -> list[Order]:
    return list(
        db.scalars(
            select(Order)
            .where(*conditions)
            .order_by(*SORTING.order_by(sort))
            .offset((page - 1) * per_page)
            .limit(per_page)
        ).all()
    )
