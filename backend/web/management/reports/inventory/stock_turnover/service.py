"""Turnover per ingredient: usage pace, days of stock left, status, and suggested purchase."""
from dataclasses import replace
from datetime import date
from decimal import ROUND_CEILING, Decimal

from sqlalchemy.orm import Session

from app.core.stock_balances import idle_days
from app.core.money import ZERO, decimal_of
from app.core import stock_balances
from app.core.sorting import RowSorting
from app.models.ingredient import INGREDIENT_OUT, INGREDIENT_RND, INGREDIENT_WASTE
from web.management.reports.common import CENT
from web.management.reports.inventory import movements
from web.management.reports.inventory.constants import QTY
from web.management.reports.inventory.stock_turnover import repository
from web.management.reports.inventory.stock_turnover.domain import (
    TURNOVER_ORDER,
    Thresholds,
    TurnoverReport,
    TurnoverRow,
    TurnoverStatus,
)

# Rows without a stock-day estimate sort after every real estimate.
NO_ESTIMATE_DAYS = 10**6

SORTING: RowSorting[TurnoverRow] = RowSorting(
    keys={
        "name": lambda row: row.name,
        "unit": lambda row: row.unit,
        "stock": lambda row: row.closing_stock,
        "sold": lambda row: row.sold,
        "shrinkage": lambda row: row.shrinkage,
        "daily_usage": lambda row: row.daily_usage,
        "days_left": lambda row: row.days_of_stock,
        "turnover": lambda row: row.turnover,
        "idle_days": lambda row: row.days_since_movement,
        "value": lambda row: row.stock_value,
        "suggested": lambda row: row.suggested_purchase,
        "status": lambda row: TURNOVER_ORDER[row.status],
    },
    identity=lambda row: row.ingredient_id,
)


def sorted_report(report: TurnoverReport, sort: str | None) -> TurnoverReport:
    return replace(report, rows=SORTING.apply(report.rows, sort))


def _turnover_status(
    closing: Decimal, days_of_stock: int | None, days_since: int | None, thresholds: Thresholds
) -> TurnoverStatus:
    """Checked in order of urgency; an empty ingredient is out, never dormant, since no money sits in it."""
    if closing <= 0:
        return TurnoverStatus.OUT
    if days_since is None or days_since >= thresholds.dormant_days:
        return TurnoverStatus.DORMANT
    if days_of_stock is not None and days_of_stock <= thresholds.urgent_days:
        return TurnoverStatus.URGENT
    if days_of_stock is not None and days_of_stock > thresholds.slow_days:
        return TurnoverStatus.SLOW
    return TurnoverStatus.SAFE


def turnover_report(
    db: Session, outlet_id: str | None, start: date, end: date, thresholds: Thresholds
) -> TurnoverReport:
    """Count cards are kept here: they are adjustments, which usage never sums, and the balance must be what is on the shelf.

    Values use today's unit price, since outgoing cards carry no price.
    """
    days = (end - start).days + 1
    day_count = Decimal(days if days > 0 else 1)

    ingredients = repository.ingredient_names(db, outlet_id)
    openings = stock_balances.balances_before(db, outlet_id, start)
    period_movements = movements.movements_by_kind(db, outlet_id, start, end, skip_count_cards=False)
    last_moved = repository.last_movements(db, outlet_id)

    rows: list[TurnoverRow] = []
    total_value = ZERO
    dormant_value = ZERO
    total_suggested = ZERO
    out_count = urgent_count = dormant_count = 0

    for ingredient_id, name, category, unit, price in ingredients:
        unit_price = decimal_of(price)
        opening = openings.get(ingredient_id, ZERO)
        by_kind = period_movements.get(ingredient_id, {})

        # A cancelled order writes a positive outgoing card, so it lowers net usage.
        sold = -by_kind.get(INGREDIENT_OUT, ZERO)
        shrinkage = -(by_kind.get(INGREDIENT_WASTE, ZERO) + by_kind.get(INGREDIENT_RND, ZERO))
        usage = sold + shrinkage
        closing = opening + sum(by_kind.values(), ZERO)

        average = (opening + closing) / 2
        if average < 0:
            average = ZERO

        daily = usage / day_count if usage > 0 else ZERO
        turnover = (usage / average) if (average > 0 and usage > 0) else None
        days_of_stock = int(closing / daily) if (daily > 0 and closing > 0) else None

        last = last_moved.get(ingredient_id)
        days_since = idle_days(last)

        status = _turnover_status(closing, days_of_stock, days_since, thresholds)

        # Rounded up because buying too little runs out mid-day, which costs more than a little extra.
        needed = daily * thresholds.target_days - closing
        suggested = needed.quantize(QTY, rounding=ROUND_CEILING) if needed > 0 else ZERO

        stock_value = (closing * unit_price) if closing > 0 else ZERO
        total_value += stock_value
        total_suggested += suggested * unit_price
        if status == TurnoverStatus.OUT:
            out_count += 1
        elif status == TurnoverStatus.URGENT:
            urgent_count += 1
        elif status == TurnoverStatus.DORMANT:
            dormant_count += 1
            dormant_value += stock_value

        rows.append(
            TurnoverRow(
                ingredient_id=ingredient_id,
                name=name,
                category=category,
                unit=unit,
                unit_price=unit_price.quantize(CENT),
                opening_stock=opening.quantize(QTY),
                closing_stock=closing.quantize(QTY),
                average_stock=average.quantize(QTY),
                sold=sold.quantize(QTY),
                shrinkage=shrinkage.quantize(QTY),
                usage=usage.quantize(QTY),
                daily_usage=daily.quantize(QTY),
                turnover=turnover.quantize(CENT) if turnover is not None else None,
                days_of_stock=days_of_stock,
                days_since_movement=days_since,
                stock_value=stock_value.quantize(CENT),
                suggested_purchase=suggested,
                status=status,
            )
        )

    rows.sort(
        key=lambda row: (
            TURNOVER_ORDER[row.status],
            row.days_of_stock if row.days_of_stock is not None else NO_ESTIMATE_DAYS,
            -row.stock_value,
        )
    )

    return TurnoverReport(
        start=start,
        end=end,
        days=days,
        thresholds=thresholds,
        total_stock_value=total_value.quantize(CENT),
        out_count=out_count,
        urgent_count=urgent_count,
        dormant_count=dormant_count,
        dormant_value=dormant_value.quantize(CENT),
        total_suggested_purchase=total_suggested.quantize(CENT),
        rows=rows,
    )
