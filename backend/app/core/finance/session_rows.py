"""One row per cash session with its reconciliation; the session history screen and the tablet's own history both read it."""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.branches import outlet_names
from app.core.finance.session_totals import SessionTotals, expected_cash, totals_for
from app.core.money import decimal_of
from app.models.cash_session import CashSession, CashSessionStatus


class SessionHistoryRowOut(BaseModel):
    id: str
    outlet_id: str
    cashier_username: str
    outlet_name: str | None
    shift_code: str | None
    shift_code_color: str | None
    running: bool
    # Opened with the three money parts, so its actual cash cannot be corrected as one figure.
    three_parts: bool
    opened_at: datetime
    closed_at: datetime | None
    business_day: date
    opening_cash: Decimal
    revenue: Decimal
    cash_revenue: Decimal
    non_cash_revenue: Decimal
    expenses: Decimal
    drawer_expenses: Decimal
    other_fund_expenses: Decimal
    shopping_fund_used: Decimal
    transactions: int
    voided_transactions: int
    expected_cash: Decimal
    # Omzet yang semestinya di tangan: tunai dikurangi belanja laci dan dana belanja (SessionTotals.expected_revenue).
    expected_revenue: Decimal
    # Omzet yang dihitung kasir saat tutup; hanya sesi tiga bagian yang mengisinya.
    actual_revenue: Decimal | None = None
    # Empty while the session is still running.
    actual_cash: Decimal | None
    difference: Decimal | None
    note: str | None


def row_out(session: CashSession, username: str, branch: str | None, totals: SessionTotals) -> SessionHistoryRowOut:
    return SessionHistoryRowOut(
        id=session.id,
        outlet_id=session.outlet_id,
        cashier_username=username,
        outlet_name=branch,
        shift_code=session.shift_code,
        shift_code_color=session.shift_code_color,
        running=session.status == CashSessionStatus.OPEN,
        three_parts=session.planned_shopping is not None,
        opened_at=session.opened_at,
        closed_at=session.closed_at,
        business_day=session.business_day,
        opening_cash=decimal_of(session.opening_cash),
        revenue=totals.revenue,
        cash_revenue=totals.cash_revenue,
        non_cash_revenue=totals.non_cash_revenue,
        expenses=totals.expenses,
        drawer_expenses=totals.drawer_expenses,
        other_fund_expenses=totals.other_fund_expenses,
        shopping_fund_used=totals.shopping_fund_used,
        transactions=totals.transactions,
        voided_transactions=totals.voided_transactions,
        expected_cash=expected_cash(session, totals),
        expected_revenue=totals.expected_revenue,
        actual_revenue=session.actual_revenue,
        actual_cash=session.actual_cash,
        difference=session.difference,
        note=session.note,
    )


def rows_of(db: Session, found: list[tuple[CashSession, str]]) -> list[SessionHistoryRowOut]:
    """Sessions paired with their cashier's username, with every figure and branch name read in three queries for the whole page."""
    totals = totals_for(db, [session.id for session, _ in found])
    branches = outlet_names(db, (session.outlet_id for session, _ in found))
    return [row_out(session, username, branches.get(session.outlet_id), totals[session.id]) for session, username in found]
