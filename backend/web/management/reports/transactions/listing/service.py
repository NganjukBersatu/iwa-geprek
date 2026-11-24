"""Builds the paged transaction list."""
from datetime import date

from sqlalchemy.orm import Session

from app.core.business_days import orders_in
from app.core.money import decimal_of
from web.management.reports.common import from_today, user_usernames
from web.management.reports.transactions.listing import repository
from web.management.reports.transactions.listing.domain import MethodTotal, TransactionPage


def transactions(
    db: Session,
    start: date | None,
    end: date | None,
    group: str,
    method: str | None,
    include_voided: bool,
    sort: str | None,
    page: int,
    per_page: int,
    outlet_id: str | None,
) -> TransactionPage:
    """Cash means the cash method or no method at all, the same rule as closing a cash session."""
    start, end = from_today(start, end)
    window = orders_in(start, end, outlet_id)
    by_method = [
        MethodTotal(code=code, label=label or code.capitalize(), count=int(count), amount=decimal_of(amount))
        for code, label, count, amount in repository.method_totals(db, window)
    ]
    conditions = repository.transaction_conditions(window, group, method, include_voided)
    count, amount = repository.transaction_count_and_amount(db, conditions)
    orders = repository.transaction_page(db, conditions, sort, page, per_page)
    return TransactionPage(
        start=start,
        end=end,
        group=group,
        method=method,
        count=int(count),
        amount=decimal_of(amount),
        by_method=by_method,
        page=page,
        per_page=per_page,
        orders=orders,
        cashier_names=user_usernames(db, {order.cashier_id for order in orders}),
    )
