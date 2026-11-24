"""Money in, out, and left over per cash session; the figures come from app.core.finance.session_totals."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.finance.session_totals import SessionTotals, totals_for, totals_of
from app.core.money import ZERO, decimal_of
from app.core.sorting import RowSorting
from app.models.cash_session import CashSession
from web.management.mutations import messages, repository
from web.management.mutations.schemas import MoneyEventOut, MutationDetailOut, MutationPageOut, MutationRowOut, MutationSummaryOut
from web.management.reports.common import month_to_date

NOT_FOUND = 404


def _difference(actual: Decimal | None, planned: Decimal | None, closed: bool) -> Decimal | None:
    return actual - planned if closed and actual is not None and planned is not None else None


def _row(session: CashSession, username: str, totals: SessionTotals) -> MutationRowOut:
    closed = session.actual_revenue is not None
    planned_float = session.planned_float if session.planned_float is not None else decimal_of(session.opening_cash)
    return MutationRowOut(
        session_id=session.id,
        cashier_username=username,
        shift_code=session.shift_code,
        opened_at=session.opened_at,
        closed_at=session.closed_at,
        closed=closed,
        planned_float=planned_float,
        planned_shopping=decimal_of(session.planned_shopping),
        cash_revenue=totals.cash_revenue,
        non_cash_revenue=totals.non_cash_revenue,
        drawer_expenses=totals.drawer_expenses,
        shopping_fund_used=totals.shopping_fund_used,
        other_fund_expenses=totals.other_fund_expenses,
        spending=totals.drawer_expenses + totals.shopping_fund_used + totals.other_fund_expenses,
        expected_revenue=totals.expected_revenue,
        actual_float=session.actual_float,
        actual_shopping=session.actual_shopping,
        actual_revenue=session.actual_revenue,
        float_difference=_difference(session.actual_float, planned_float, closed),
        shopping_difference=_difference(session.actual_shopping, session.planned_shopping, closed),
        revenue_difference=_difference(session.actual_revenue, totals.expected_revenue, closed),
    )


def _sum(rows: list[MutationRowOut], field: str) -> Decimal:
    return sum((getattr(row, field) or ZERO for row in rows), ZERO)


SORTING: RowSorting[MutationRowOut] = RowSorting(
    keys={
        "cashier": lambda row: row.cashier_username,
        "opened_at": lambda row: row.opened_at,
        "cash_revenue": lambda row: row.cash_revenue,
        "non_cash_revenue": lambda row: row.non_cash_revenue,
        "spending": lambda row: row.spending,
        "revenue_difference": lambda row: row.revenue_difference,
    },
    identity=lambda row: row.session_id,
)


def page(db: Session, start: date | None, end: date | None, outlet_id: str | None, sort: str | None, number: int, size: int) -> MutationPageOut:
    start, end = month_to_date(start, end)
    found = repository.three_part_sessions(db, start, end, outlet_id)
    totals = totals_for(db, [session.id for session, _ in found])
    rows = [_row(session, username, totals[session.id]) for session, username in found]
    summary = MutationSummaryOut(
        sessions=len(rows),
        closed=sum(1 for row in rows if row.closed),
        cash_revenue=_sum(rows, "cash_revenue"),
        non_cash_revenue=_sum(rows, "non_cash_revenue"),
        drawer_expenses=_sum(rows, "drawer_expenses"),
        shopping_fund_used=_sum(rows, "shopping_fund_used"),
        other_fund_expenses=_sum(rows, "other_fund_expenses"),
        float_difference=_sum(rows, "float_difference"),
        shopping_difference=_sum(rows, "shopping_difference"),
        revenue_difference=_sum(rows, "revenue_difference"),
    )
    rows = SORTING.apply(rows, sort)
    first = (number - 1) * size
    return MutationPageOut(
        start=start, end=end, items=rows[first : first + size], total=len(rows), page=number, size=size, summary=summary
    )


def detail(db: Session, session_id: str, outlet_id: str | None) -> MutationDetailOut:
    """The money events of one session in time order: opening, every purchase, closing."""
    found = repository.find_with_cashier(db, session_id)
    # Another branch's session answers as missing, so its existence is not revealed.
    if found is None or found[0].planned_shopping is None or (outlet_id and found[0].outlet_id != outlet_id):
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    session, username = found
    events = [MoneyEventOut(at=session.opened_at, kind="open", description=None, fund_source=None, amount=decimal_of(session.opening_cash))]
    for expense in repository.expenses_of(db, session.id):
        events.append(
            MoneyEventOut(
                at=expense.created_at, kind="expense", description=expense.item_name, fund_source=expense.fund_source.value, amount=expense.amount
            )
        )
    if session.closed_at is not None and session.actual_revenue is not None:
        counted = decimal_of(session.actual_float) + decimal_of(session.actual_shopping) + decimal_of(session.actual_revenue)
        events.append(MoneyEventOut(at=session.closed_at, kind="close", description=None, fund_source=None, amount=counted))
    return MutationDetailOut(session=_row(session, username, totals_of(db, session.id)), events=events)
