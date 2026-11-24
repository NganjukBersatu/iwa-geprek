"""The one door for the money of a cash session; closing a session, its history and the mutation screen all read it."""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import ColumnElement, case, func, select
from sqlalchemy.sql.selectable import ScalarSelect
from sqlalchemy.orm import Session

from app.core.money import ZERO, decimal_of
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.expense import Expense, FundSource
from app.models.order import CASH_METHOD, Order


@dataclass(frozen=True)
class SessionTotals:
    revenue: Decimal
    cash_revenue: Decimal
    non_cash_revenue: Decimal
    drawer_expenses: Decimal
    other_fund_expenses: Decimal
    shopping_fund_used: Decimal
    transactions: int
    voided_transactions: int

    @property
    def expenses(self) -> Decimal:
        """The shopping fund is kept apart and never counts as an expense of the till."""
        return self.drawer_expenses + self.other_fund_expenses

    @property
    def expected_revenue(self) -> Decimal:
        """Revenue that should be in hand at closing: cash sales less drawer and shopping-fund purchases."""
        return self.cash_revenue - self.drawer_expenses - self.shopping_fund_used


EMPTY = SessionTotals(ZERO, ZERO, ZERO, ZERO, ZERO, ZERO, 0, 0)

# A voided order was refunded, so it never counts as revenue.
VALID_ORDER = Order.voided_at.is_(None)
TILL_SOURCES = (FundSource.DRAWER_CASH, FundSource.OTHER_FUNDS)


def revenue_column(session_id: ColumnElement[str]) -> ScalarSelect:
    """The same revenue as totals_for, as a column a list can be ordered by."""
    return select(func.coalesce(func.sum(Order.total), 0)).where(Order.cash_session_id == session_id, VALID_ORDER).scalar_subquery()


def expenses_column(session_id: ColumnElement[str]) -> ScalarSelect:
    """The same spending as SessionTotals.expenses, as a column a list can be ordered by."""
    return select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.cash_session_id == session_id, Expense.fund_source.in_(TILL_SOURCES)).scalar_subquery()


def expected_cash(session: CashSession, totals: SessionTotals) -> Decimal:
    """Only money that went through the drawer is compared with it: non-cash sales go to the bank, other funds to another pocket."""
    return decimal_of(session.opening_cash) + totals.cash_revenue - totals.drawer_expenses


def totals_for(db: Session, session_ids: list[str]) -> dict[str, SessionTotals]:
    """Totals of many sessions in two grouped queries; a voided order was refunded, so it never counts as revenue."""
    if not session_ids:
        return {}
    valid = VALID_ORDER
    sales = db.execute(
        select(
            Order.cash_session_id,
            func.sum(case((valid, Order.total), else_=0)),
            func.sum(case((valid & Order.is_cash(), Order.total), else_=0)),
            func.sum(case((valid, 1), else_=0)),
            func.sum(case((~valid, 1), else_=0)),
        )
        .where(Order.cash_session_id.in_(session_ids))
        .group_by(Order.cash_session_id)
    ).all()
    spending = db.execute(
        select(Expense.cash_session_id, Expense.fund_source, func.sum(Expense.amount))
        .where(Expense.cash_session_id.in_(session_ids))
        .group_by(Expense.cash_session_id, Expense.fund_source)
    ).all()

    by_source: dict[str, dict[FundSource, Decimal]] = {}
    for session_id, source, amount in spending:
        by_source.setdefault(session_id, {})[source] = decimal_of(amount)
    sold = {row[0]: row for row in sales}

    result = {}
    for session_id in session_ids:
        _, revenue, cash, count, voided = sold.get(session_id, (session_id, 0, 0, 0, 0))
        sources = by_source.get(session_id, {})
        revenue, cash = decimal_of(revenue), decimal_of(cash)
        result[session_id] = SessionTotals(
            revenue=revenue,
            cash_revenue=cash,
            non_cash_revenue=revenue - cash,
            drawer_expenses=sources.get(FundSource.DRAWER_CASH, ZERO),
            other_fund_expenses=sources.get(FundSource.OTHER_FUNDS, ZERO),
            shopping_fund_used=sources.get(FundSource.SHOPPING_FUND, ZERO),
            transactions=int(count or 0),
            voided_transactions=int(voided or 0),
        )
    return result


@dataclass(frozen=True)
class MethodTotal:
    """Revenue of one payment method in a session; two bank accounts are two methods, each with its own label."""

    method_id: str | None
    label: str
    cash: bool
    amount: Decimal
    transactions: int


# Pesanan lama tanpa metode tercatat dianggap tunai, sama dengan Order.is_cash.
CASH_LABEL = "Tunai"


def method_totals(db: Session, session_id: str) -> list[MethodTotal]:
    """Valid orders of one session grouped by the method chosen at payment, largest first; one query on the session's own orders."""
    rows = db.execute(
        select(Order.payment_method_id, Order.payment_method_label, Order.payment_method, func.sum(Order.total), func.count())
        .where(Order.cash_session_id == session_id, VALID_ORDER)
        .group_by(Order.payment_method_id, Order.payment_method_label, Order.payment_method)
    ).all()
    amounts: dict[tuple[str | None, str, bool], Decimal] = {}
    counts: dict[tuple[str | None, str, bool], int] = {}
    for method_id, label, code, amount, count in rows:
        cash = code is None or code == CASH_METHOD
        # Semua tunai disatukan; non tunai dibedakan per metode supaya tiap rekening tampil sendiri.
        key = (None, label or CASH_LABEL, True) if cash else (method_id, label or code, False)
        amounts[key] = amounts.get(key, ZERO) + decimal_of(amount)
        counts[key] = counts.get(key, 0) + int(count or 0)
    totals = [MethodTotal(method_id=key[0], label=key[1], cash=key[2], amount=amounts[key], transactions=counts[key]) for key in amounts]
    return sorted(totals, key=lambda total: (-total.amount, total.label))


def totals_of(db: Session, session_id: str) -> SessionTotals:
    return totals_for(db, [session_id]).get(session_id, EMPTY)


def refresh_closed(db: Session, session: CashSession) -> None:
    """After a correction, a closed session's frozen figures are worked out again; an open one keeps none, so nothing changes."""
    if session.status != CashSessionStatus.CLOSED:
        return
    db.flush()
    totals = totals_of(db, session.id)
    session.system_revenue = totals.revenue
    session.cash_revenue = totals.cash_revenue
    session.drawer_expenses = totals.drawer_expenses
    if session.planned_shopping is not None and session.actual_revenue is not None:
        # One equivalent figure, so actual minus expected still equals the sum of the three parts' differences.
        session.actual_cash = (
            decimal_of(session.actual_float)
            + decimal_of(session.actual_revenue)
            + totals.shopping_fund_used
            + (decimal_of(session.actual_shopping) - decimal_of(session.planned_shopping))
        )
    if session.actual_cash is not None:
        session.difference = session.actual_cash - expected_cash(session, totals)
