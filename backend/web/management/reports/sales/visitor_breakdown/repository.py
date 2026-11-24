"""Database reads for the visitor breakdown."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.core.business_days import valid_orders_in


def tallies_between(db: Session, start: date, end: date, outlet_id: str | None) -> list[tuple]:
    """(business day, category label, gender label, orders, revenue) of the orders that were not voided: one grouped query, however many orders there are."""
    day = Order.business_day
    return list(
        db.execute(
            select(day, Order.visitor_category_label, Order.visitor_gender_label, func.count(), func.sum(Order.total))
            .where(
                *valid_orders_in(start, end, outlet_id),
            )
            .group_by(day, Order.visitor_category_label, Order.visitor_gender_label)
        ).all()
    )
