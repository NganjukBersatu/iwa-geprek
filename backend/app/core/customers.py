"""Registered customers as the cashier meets them: suggestions while typing a name or a phone number, and the visit a finished order counts as."""
import uuid
from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core import search
from app.core.clock import local_date, now
from app.models.customer import Customer
from app.models.visit import Visit

PERMISSION_VIEW = "pelanggan.lihat"
SUGGESTION_LIMIT = 6
VISIT_SOURCE_ORDER = "order"


@dataclass(frozen=True)
class Suggestion:
    id: str
    name: str
    contact: str | None
    visit_count: int


def suggest(db: Session, text: str) -> list[Suggestion]:
    """Active customers whose name or contact matches what was typed, the most frequent visitors first."""
    typed = text.strip()
    if not typed:
        return []
    visits = (
        select(Visit.customer_id, func.count(Visit.id).label("count"))
        .group_by(Visit.customer_id)
        .subquery()
    )
    rows = db.execute(
        select(Customer.id, Customer.name, Customer.contact, func.coalesce(visits.c.count, 0))
        .outerjoin(visits, visits.c.customer_id == Customer.id)
        .where(Customer.is_active.is_(True), or_(search.contains(Customer.name, typed), search.contains(Customer.contact, typed)))
        .order_by(func.coalesce(visits.c.count, 0).desc(), Customer.name, Customer.id)
        .limit(SUGGESTION_LIMIT)
    ).all()
    return [Suggestion(id=row[0], name=row[1], contact=row[2], visit_count=int(row[3])) for row in rows]


def linked(db: Session, customer_id: str | None) -> Customer | None:
    """A customer removed while the cashier was filling the order leaves the sale a walk-in, never refused."""
    return db.get(Customer, customer_id) if customer_id else None


def count_visit(db: Session, customer_id: str, outlet_id: str) -> None:
    """At most one visit per customer per branch per day, so two receipts at one sitting are one visit; does not commit."""
    today = local_date(now())
    for visited_at in db.scalars(
        select(Visit.visited_at).where(Visit.customer_id == customer_id, Visit.outlet_id == outlet_id).order_by(Visit.visited_at.desc()).limit(1)
    ):
        if local_date(visited_at) == today:
            return
    db.add(Visit(id=str(uuid.uuid4()), outlet_id=outlet_id, customer_id=customer_id, source=VISIT_SOURCE_ORDER, visited_at=now()))
