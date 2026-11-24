"""Builds the daily overview: income and spending per business day, so a day always equals the sum of its sessions."""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from web.management.reports.common import month_to_date, percent_tenth
from web.management.reports.sales.daily_overview import repository
from web.management.reports.sales.daily_overview.domain import DailyOverview, DailyRow, DailyTotals

_CASH_IN, _OTHER_IN, _CASH_OUT, _OTHER_OUT = "cash_in", "other_in", "cash_out", "other_out"


def _empty_day() -> dict[str, Decimal]:
    return {_CASH_IN: Decimal("0"), _OTHER_IN: Decimal("0"), _CASH_OUT: Decimal("0"), _OTHER_OUT: Decimal("0")}


def _day_totals(sums: dict[str, Decimal]) -> dict:
    income = sums[_CASH_IN] + sums[_OTHER_IN]
    expense = sums[_CASH_OUT] + sums[_OTHER_OUT]
    return {
        "cash_income": sums[_CASH_IN],
        "non_cash_income": sums[_OTHER_IN],
        "income_total": income,
        "cash_expense": sums[_CASH_OUT],
        "non_cash_expense": sums[_OTHER_OUT],
        "expense_total": expense,
        "expense_percent": percent_tenth(expense, income),
        "cash_profit": sums[_CASH_IN] - sums[_CASH_OUT],
        "non_cash_profit": sums[_OTHER_IN] - sums[_OTHER_OUT],
        "profit_total": income - expense,
        "profit_percent": percent_tenth(income - expense, income),
    }


def cash_profit_by_outlet(db: Session, start: date, end: date, outlet_ids: list[str]) -> dict[str, dict[date, Decimal]]:
    """Cash income minus drawer cash spent, per day, for each branch: two grouped queries however many branches there are."""
    profit: dict[str, dict[date, Decimal]] = {outlet_id: {} for outlet_id in outlet_ids}
    for outlet_id, day, kind, total in repository.order_totals_by_outlet(db, start, end, outlet_ids):
        if kind == repository.CASH:
            profit[outlet_id][day] = profit[outlet_id].get(day, Decimal("0")) + total
    for outlet_id, day, kind, total in repository.expense_totals_by_outlet(db, start, end, outlet_ids):
        if kind == repository.CASH:
            profit[outlet_id][day] = profit[outlet_id].get(day, Decimal("0")) - total
    return profit


def daily_overview(db: Session, start: date | None, end: date | None, outlet_id: str | None) -> DailyOverview:
    """Cash-flow profit per business day, not cost-of-goods profit; defaults to the month so far."""
    start, end = month_to_date(start, end)

    by_day: dict[date, dict[str, Decimal]] = {}
    for day, kind, total in repository.order_totals(db, start, end, outlet_id):
        by_day.setdefault(day, _empty_day())[_CASH_IN if kind == repository.CASH else _OTHER_IN] += total
    for day, kind, total in repository.expense_totals(db, start, end, outlet_id):
        by_day.setdefault(day, _empty_day())[_CASH_OUT if kind == repository.CASH else _OTHER_OUT] += total

    rows = []
    grand = _empty_day()
    day = start
    while day <= end:
        sums = by_day.get(day, _empty_day())
        rows.append(DailyRow(date=day, **_day_totals(sums)))
        for key in grand:
            grand[key] += sums[key]
        day += timedelta(days=1)
    return DailyOverview(start=start, end=end, rows=rows, total=DailyTotals(**_day_totals(grand)))
