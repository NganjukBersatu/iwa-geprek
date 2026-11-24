"""Builds the cashier report: sales, spending, and drawer difference per cashier, each counted on its business day."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from web.management.reports.common import from_today, user_usernames
from web.management.reports.sales import messages
from web.management.reports.sales.cashiers import repository
from web.management.reports.sales.cashiers.domain import CashierReport, CashierRow


def cashier_report(db: Session, start: date | None, end: date | None, outlet_id: str | None) -> CashierReport:
    """Sales, purchases, and drawer difference per cashier, aggregated separately so joins cannot multiply sums."""
    start, end = from_today(start, end)
    sold = repository.sales_by_cashier(db, start, end, outlet_id)
    voided = repository.voids_by_cashier(db, start, end, outlet_id)
    spent = repository.expenses_by_cashier(db, start, end, outlet_id)
    sessions = repository.closed_sessions_by_cashier(db, start, end, outlet_id)

    involved = set(sold) | set(voided) | set(spent) | set(sessions)
    if not involved:
        return CashierReport(start=start, end=end, cashiers=[])

    usernames = user_usernames(db, involved)
    rows = []
    for cashier_id in involved:
        count, total, cash = sold.get(cashier_id, (0, Decimal("0"), Decimal("0")))
        session_count, difference = sessions.get(cashier_id, (0, Decimal("0")))
        rows.append(
            CashierRow(
                cashier_id=cashier_id,
                # A deleted account keeps its row: its sales were real.
                username=usernames.get(cashier_id, messages.DELETED_ACCOUNT),
                transaction_count=count,
                voided_count=voided.get(cashier_id, 0),
                sales_total=total,
                cash_total=cash,
                non_cash_total=total - cash,
                expense_total=spent.get(cashier_id, Decimal("0")),
                session_count=session_count,
                difference_total=difference,
            )
        )
    rows.sort(key=lambda row: (-row.sales_total, row.username))
    return CashierReport(start=start, end=end, cashiers=rows)
