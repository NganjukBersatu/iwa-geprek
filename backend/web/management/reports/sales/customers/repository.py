"""Database reads of the customer report; every aggregate passes through branch_filter."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.date_range import range_end, range_start
from app.core.money import decimal_of
from app.core.search import contains
from app.models.customer import Customer
from app.models.order import Order
from app.models.visit import Visit
from app.core.branches import branch_filter
from app.core.business_days import valid_orders_in


def visitor_page(
    db: Session, start: date, end: date, outlet_id: str | None, search: str | None, page: int, size: int
) -> tuple[int, list[tuple]]:
    """Total matches and one page of (customer, visit count, first visit, last visit), latest visitor first."""
    in_range = (
        Visit.visited_at >= range_start(start),
        Visit.visited_at < range_end(end),
        *branch_filter(Visit.outlet_id, outlet_id),
    )
    visits = (
        select(
            Visit.customer_id.label("customer_id"),
            func.count().label("count"),
            func.min(Visit.visited_at).label("first"),
            func.max(Visit.visited_at).label("last"),
        )
        .where(*in_range)
        .group_by(Visit.customer_id)
        .subquery()
    )
    query = select(Customer, visits.c.count, visits.c.first, visits.c.last).join(
        visits, visits.c.customer_id == Customer.id
    )
    if search:
        query = query.where(contains(Customer.name, search))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(
        query.order_by(visits.c.last.desc(), Customer.id).offset((page - 1) * size).limit(size)
    ).all()
    return total, list(rows)


def visited_before(db: Session, customer_ids: list[str], before: datetime) -> set[str]:
    return set(
        db.scalars(
            select(Visit.customer_id).where(Visit.customer_id.in_(customer_ids), Visit.visited_at < before).distinct()
        ).all()
    )


def spending_of(
    db: Session, customer_ids: list[str], start: date, end: date, outlet_id: str | None
) -> dict[str, tuple[int, Decimal]]:
    return {
        customer_id: (count, decimal_of(total))
        for customer_id, count, total in db.execute(
            select(Order.customer_id, func.count(), func.sum(Order.total))
            .where(
                Order.customer_id.in_(customer_ids),
                *valid_orders_in(start, end, outlet_id),
            )
            .group_by(Order.customer_id)
        ).all()
    }
