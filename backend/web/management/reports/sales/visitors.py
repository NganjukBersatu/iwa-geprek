"""Visitor counts of a range, shared by the summary and the customer report."""
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.date_range import range_end, range_start
from app.models.visit import Visit
from app.core.branches import branch_filter


@dataclass(frozen=True)
class Customers:
    """New plus returning always equals unique, since returning means a visit before the range."""

    visits: int
    unique: int
    new: int
    returning: int


def _customer_counts(db: Session, start: date, end: date, outlet_id: str | None) -> tuple[int, int, int]:
    """Visits, unique visitors, and visitors who had visited (at any branch) before the range."""
    first = range_start(start)
    in_range = (
        Visit.visited_at >= first,
        Visit.visited_at < range_end(end),
        *branch_filter(Visit.outlet_id, outlet_id),
    )
    visits = db.scalar(select(func.count()).select_from(Visit).where(*in_range)) or 0
    unique = db.scalar(select(func.count(func.distinct(Visit.customer_id))).where(*in_range)) or 0

    came = select(Visit.customer_id.label("cid")).where(*in_range).distinct().subquery()
    visited_before = select(1).where(Visit.customer_id == came.c.cid, Visit.visited_at < first).exists()
    returning = db.scalar(select(func.count()).select_from(came).where(visited_before)) or 0
    return visits, unique, returning


def customers(db: Session, start: date, end: date, outlet_id: str | None) -> Customers:
    """Counted from visits, not orders: the owner wants to know who came, which is what the camera records."""
    visits, unique, returning = _customer_counts(db, start, end, outlet_id)
    return Customers(visits=visits, unique=unique, new=unique - returning, returning=returning)
