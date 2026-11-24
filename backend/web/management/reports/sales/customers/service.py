"""Builds the customer report; figures and ordering match the legacy /laporan routes exactly."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.date_range import range_start
from web.management.reports.common import from_today
from web.management.reports.sales.customers import repository
from web.management.reports.sales.customers.constants import CUSTOMER_ACTIVE, CUSTOMER_INACTIVE
from web.management.reports.sales.customers.domain import CustomerReport, CustomerVisit
from web.management.reports.sales.visitors import customers


def customer_report(
    db: Session,
    start: date | None,
    end: date | None,
    outlet_id: str | None,
    search: str | None,
    page: int,
    size: int,
) -> CustomerReport:
    """Who came in the range, with their visits and spending inside it."""
    start, end = from_today(start, end)
    total, rows = repository.visitor_page(db, start, end, outlet_id, search, page, size)

    ids = [customer.id for customer, *_ in rows]
    if ids:
        returning = repository.visited_before(db, ids, range_start(start))
        spending = repository.spending_of(db, ids, start, end, outlet_id)
    else:
        returning, spending = set(), {}

    items = []
    for customer, visit_count, first_visit_at, last_visit_at in rows:
        transaction_count, total_spent = spending.get(customer.id, (0, Decimal("0")))
        items.append(
            CustomerVisit(
                customer_id=customer.id,
                name=customer.name,
                contact=customer.contact,
                status=CUSTOMER_ACTIVE if customer.is_active else CUSTOMER_INACTIVE,
                visit_count=visit_count,
                first_visit_at=first_visit_at,
                last_visit_at=last_visit_at,
                is_new=customer.id not in returning,
                transaction_count=transaction_count,
                total_spent=total_spent,
            )
        )
    return CustomerReport(
        start=start,
        end=end,
        summary=customers(db, start, end, outlet_id),
        items=items,
        total=total,
        page=page,
        size=size,
    )
