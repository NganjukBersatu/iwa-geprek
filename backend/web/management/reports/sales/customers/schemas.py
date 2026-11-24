from datetime import date, datetime
from decimal import Decimal

from web.management.reports.sales.response import CustomersOut, ResponseModel


class CustomerVisitOut(ResponseModel):
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


class CustomerReportOut(ResponseModel):
    start: date
    end: date
    summary: CustomersOut
    items: list[CustomerVisitOut]
    total: int
    page: int
    size: int
