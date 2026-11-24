"""Money: income against spending, till sessions, deposits, non-cash checks, overpayments, voids and void requests."""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.core.business_days import first_unfinished_day
from app.core.finance import deposited
from app.core.money import ZERO, decimal_of
from app.core.orders.cancellations import waiting
from app.core.user_names import user_names
from app.models.cancellation_request import CancellationRequest
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.order import Order
from app.models.overpayment import Overpayment
from web.management.deposits.service import due_by_outlet
from web.management.issues import constants as c
from web.management.issues.domain import Issue, IssueKind, IssueLevel, Scope
from web.management.non_cash_checks import repository as non_cash
from web.management.reports.sales.daily_overview import repository as daily


def expense_over_income(scope: Scope) -> list[Issue]:
    """Finished business days only, since a day still running has spent before it sold. amount: spent, compared: income."""
    unfinished = first_unfinished_day(scope.db, scope.outlet_ids)
    end = scope.today - timedelta(days=1)
    start = end - timedelta(days=c.EVENT_DAYS - 1)
    income: dict[tuple[str, date], Decimal] = {}
    spent: dict[tuple[str, date], Decimal] = {}
    for outlet_id, day, _kind, total in daily.order_totals_by_outlet(scope.db, start, end, scope.outlet_ids):
        income[(outlet_id, day)] = income.get((outlet_id, day), ZERO) + total
    for outlet_id, day, _kind, total in daily.expense_totals_by_outlet(scope.db, start, end, scope.outlet_ids):
        spent[(outlet_id, day)] = spent.get((outlet_id, day), ZERO) + total
    return [
        Issue(IssueKind.EXPENSE_OVER_INCOME, IssueLevel.WARNING, outlet_id, None, "", day=day, amount=amount, compared=income.get((outlet_id, day), ZERO))
        for (outlet_id, day), amount in spent.items()
        if day < unfinished[outlet_id] and amount > income.get((outlet_id, day), ZERO)
    ]


def closed_sessions(scope: Scope) -> list[Issue]:
    """Closed sessions of the last business days: cash difference (amount), drawer spending above cash income (amount, compared),
    and float or shopping money that differs from the plan (amount: actual, compared: planned)."""
    rows = scope.db.scalars(
        select(CashSession).where(
            CashSession.outlet_id.in_(scope.outlet_ids),
            CashSession.status == CashSessionStatus.CLOSED,
            CashSession.business_day >= scope.first_day(c.EVENT_DAYS),
        )
    ).all()
    names = user_names(scope.db, (row.cashier_id for row in rows))
    issues: list[Issue] = []
    for row in rows:
        cashier = names.get(row.cashier_id, "")
        common = dict(outlet_id=row.outlet_id, subject_id=row.id, subject=cashier, at=row.closed_at)
        difference = decimal_of(row.difference) if row.difference is not None else None
        if difference is not None and abs(difference) > c.CASH_DIFFERENCE_LIMIT:
            issues.append(Issue(IssueKind.CASH_DIFFERENCE, IssueLevel.PROBLEM, amount=difference, **common))
        if decimal_of(row.drawer_expenses) > decimal_of(row.cash_revenue):
            issues.append(Issue(IssueKind.DRAWER_OVER_CASH, IssueLevel.WARNING, amount=decimal_of(row.drawer_expenses), compared=decimal_of(row.cash_revenue), **common))
        for kind, planned, actual in (
            (IssueKind.FLOAT_DIFFERENCE, row.planned_float, row.actual_float),
            (IssueKind.SHOPPING_DIFFERENCE, row.planned_shopping, row.actual_shopping),
        ):
            if planned is not None and actual is not None and decimal_of(planned) != decimal_of(actual):
                issues.append(Issue(kind, IssueLevel.WARNING, amount=decimal_of(actual), compared=decimal_of(planned), **common))
    return issues


def sessions_left_open(scope: Scope) -> list[Issue]:
    """at: when it was opened."""
    rows = scope.db.scalars(
        select(CashSession).where(
            CashSession.outlet_id.in_(scope.outlet_ids),
            CashSession.status == CashSessionStatus.OPEN,
            CashSession.opened_at < scope.now - timedelta(hours=c.SESSION_OPEN_HOURS),
        )
    ).all()
    names = user_names(scope.db, (row.cashier_id for row in rows))
    return [Issue(IssueKind.SESSION_LEFT_OPEN, IssueLevel.PROBLEM, row.outlet_id, row.id, names.get(row.cashier_id, ""), at=row.opened_at) for row in rows]


def deposits_held(scope: Scope) -> list[Issue]:
    """One per branch. amount: still held, count: days not settled, day: the oldest of them."""
    start = scope.first_day(c.MONEY_LOOKBACK_DAYS)
    end = scope.today - timedelta(days=c.DEPOSIT_LATE_DAYS + 1)
    if end < start:
        return []
    due = due_by_outlet(scope.db, scope.outlet_ids, start, end)
    paid = deposited.paid_by_outlet(scope.db, scope.outlet_ids, start, end)
    issues: list[Issue] = []
    for outlet_id in scope.outlet_ids:
        held = {day: left for day, owed in due.get(outlet_id, {}).items() if (left := owed - paid[outlet_id].get(day, ZERO)) > 0}
        if held:
            issues.append(Issue(IssueKind.DEPOSIT_HELD, IssueLevel.WARNING, outlet_id, None, "", day=min(held), amount=sum(held.values(), ZERO), count=len(held)))
    return issues


def non_cash_checks(scope: Scope) -> list[Issue]:
    """Unchecked: one per branch (amount: recorded, count: days, day: the oldest). Mismatch: one per day (amount: bank minus recorded)."""
    start = scope.first_day(c.MONEY_LOOKBACK_DAYS)
    late = scope.today - timedelta(days=c.NON_CASH_LATE_DAYS + 1)
    recent = scope.first_day(c.EVENT_DAYS)
    recorded = non_cash.recorded_by_outlet(scope.db, scope.outlet_ids, start, scope.today)
    checks = non_cash.checks_by_outlet(scope.db, scope.outlet_ids, start, scope.today)
    issues: list[Issue] = []
    for outlet_id in scope.outlet_ids:
        unchecked = {day: total for day, total in recorded[outlet_id].items() if day <= late and total > 0 and day not in checks[outlet_id]}
        if unchecked:
            issues.append(Issue(IssueKind.NON_CASH_UNCHECKED, IssueLevel.WARNING, outlet_id, None, "", day=min(unchecked), amount=sum(unchecked.values(), ZERO), count=len(unchecked)))
        for day, check in checks[outlet_id].items():
            difference = decimal_of(check.bank_amount) - recorded[outlet_id].get(day, ZERO)
            if day >= recent and difference != 0:
                issues.append(Issue(IssueKind.NON_CASH_MISMATCH, IssueLevel.WARNING, outlet_id, None, "", day=day, amount=difference))
    return issues


def overpayments(scope: Scope) -> list[Issue]:
    """amount: paid beyond the total, unit: the payment method."""
    rows = scope.db.scalars(select(Overpayment).where(Overpayment.outlet_id.in_(scope.outlet_ids), Overpayment.business_day >= scope.first_day(c.EVENT_DAYS))).all()
    return [
        Issue(IssueKind.OVERPAYMENT, IssueLevel.WARNING, row.outlet_id, row.order_id, row.cashier_name, at=row.recorded_at, amount=decimal_of(row.amount), unit=row.method_label)
        for row in rows
    ]


def voids_many(scope: Scope) -> list[Issue]:
    """One per cashier and day of the order, which the branch and date index can read. count: orders voided."""
    day = Order.business_day
    rows = scope.db.execute(
        select(Order.outlet_id, Order.cashier_id, day, func.count(Order.id))
        .where(Order.outlet_id.in_(scope.outlet_ids), Order.business_day >= scope.first_day(c.EVENT_DAYS), Order.voided_at.is_not(None))
        .group_by(Order.outlet_id, Order.cashier_id, day)
        .having(func.count(Order.id) >= c.VOIDS_PER_CASHIER_DAY)
    ).all()
    names = user_names(scope.db, (cashier_id for _, cashier_id, _, _ in rows))
    return [
        Issue(IssueKind.VOIDS_MANY, IssueLevel.WARNING, outlet_id, cashier_id, names.get(cashier_id, ""), day=voided_on, count=count)
        for outlet_id, cashier_id, voided_on, count in rows
    ]


def cancellations_waiting(scope: Scope) -> list[Issue]:
    """One per branch. count: requests waiting."""
    rows = scope.db.execute(
        select(CancellationRequest.outlet_id, func.count(CancellationRequest.id))
        .where(waiting(), CancellationRequest.outlet_id.in_(scope.outlet_ids))
        .group_by(CancellationRequest.outlet_id)
    ).all()
    return [Issue(IssueKind.CANCELLATION_WAITING, IssueLevel.PROBLEM, outlet_id, None, "", count=count) for outlet_id, count in rows]
