"""What the customer report service hands to the mappers."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from web.management.reports.sales.visitors import Customers


@dataclass(frozen=True)
class CustomerVisit:
    customer_id: str
    name: str
    contact: str | None
    status: str
    visit_count: int
    first_visit_at: datetime
    last_visit_at: datetime
    is_new: bool
    transaction_count: int
    total_spent: Decimal


@dataclass(frozen=True)
class CustomerReport:
    start: date
    end: date
    summary: Customers
    items: list[CustomerVisit]
    total: int
    page: int
    size: int
