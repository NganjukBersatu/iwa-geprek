"""HTTP surface of the transaction list."""
from fastapi import APIRouter, Depends, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_gate
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.models.user import User
from web.management.reports.common import as_http
from web.management.reports.transactions.listing import service
from web.management.reports.transactions.listing.mappers import transactions_out
from web.management.reports.transactions.listing.schemas import TransactionGroup, TransactionsOut
from web.management.reports.transactions.paging import DEFAULT_PER_PAGE, MAX_PER_PAGE
from app.core.sorting import Sort
from web.management.reports import gates

router = APIRouter(prefix="/reports/transactions", tags=["v2-reports"])

SHAPE = TypeAdapter(TransactionsOut)


@router.get("", response_model=TransactionsOut)
def transactions(
    start: Day | None = Query(None, description="Defaults to today"),
    end: Day | None = Query(None, description="Defaults to start"),
    group: TransactionGroup = Query("all"),
    method: str | None = Query(None, description="Payment method code; empty means every method"),
    include_voided: bool = Query(False),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(DEFAULT_PER_PAGE, ge=1, le=MAX_PER_PAGE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.TRANSACTION_LIST)),
):
    """Per-method totals cover the whole range of valid orders, ignoring the group and method filters."""
    try:
        return cache.read(
            "web.reports.transactions",
            (start, end, group, method, include_voided, sort, page, per_page, outlet_id),
            lambda: transactions_out(service.transactions(db, start, end, group, method, include_voided, sort, page, per_page, outlet_id)),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
