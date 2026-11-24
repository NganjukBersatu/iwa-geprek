"""Ingredient stock per period: opening, movements, closing, and the shrinkage a closed count reveals."""
from dataclasses import replace
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.money import ZERO, decimal_of
from app.core import stock_balances
from app.core.sorting import RowSorting
from app.models.ingredient import (
    INGREDIENT_ADJUSTMENT,
    INGREDIENT_IN,
    INGREDIENT_OUT,
    INGREDIENT_RND,
    INGREDIENT_WASTE,
    IngredientCountLine,
)
from web.management.reports.common import CENT
from web.management.reports.inventory import movements
from web.management.reports.inventory.constants import QTY
from web.management.reports.inventory.ingredient_stock import repository
from web.management.reports.inventory.ingredient_stock.domain import REPLACEMENT_ORDER, ReplacementStatus, StockReport, StockRow

SORTING: RowSorting[StockRow] = RowSorting(
    keys={
        "name": lambda row: row.name,
        "unit": lambda row: row.unit,
        "unit_price": lambda row: row.unit_price,
        "opening": lambda row: row.opening_stock,
        "purchased": lambda row: row.purchased,
        "used": lambda row: row.used,
        "wasted": lambda row: row.wasted,
        "rnd": lambda row: row.rnd,
        "adjustment": lambda row: row.adjustment,
        "closing": lambda row: row.closing_stock,
        "counted": lambda row: row.counted,
        "difference": lambda row: row.difference,
        "shrink_percent": lambda row: row.shrink_percent,
        "book_value": lambda row: row.book_value,
        "counted_value": lambda row: row.counted_value,
        "difference_value": lambda row: row.difference_value,
        "tolerance": lambda row: row.shrink_tolerance,
        "status": lambda row: REPLACEMENT_ORDER.index(row.replacement_status),
    },
    identity=lambda row: row.ingredient_id,
)


def sorted_report(report: StockReport, sort: str | None) -> StockReport:
    return replace(report, rows=SORTING.apply(report.rows, sort))


def stock_row(
    *,
    ingredient_id: str,
    name: str,
    category: str | None,
    unit: str,
    unit_price: Decimal,
    tolerance: Decimal,
    opening: Decimal,
    by_kind: dict[str, Decimal],
    counted: Decimal | None,
) -> StockRow:
    """One row from raw figures; reducing movements are stored negative and shown positive."""
    purchased = by_kind.get(INGREDIENT_IN, ZERO)
    used = -by_kind.get(INGREDIENT_OUT, ZERO)
    wasted = -by_kind.get(INGREDIENT_WASTE, ZERO)
    rnd = -by_kind.get(INGREDIENT_RND, ZERO)
    adjustment = by_kind.get(INGREDIENT_ADJUSTMENT, ZERO)
    closing = opening + purchased - used - wasted - rnd + adjustment
    book_value = (closing * unit_price).quantize(CENT)

    difference = shrink_percent = counted_value = difference_value = None
    if closing < 0:
        # A negative book balance is a wrong recipe or a missed purchase, not shrinkage.
        status = ReplacementStatus.CHECK
    elif counted is None:
        status = ReplacementStatus.UNCOUNTED
    else:
        difference = (counted - closing).quantize(QTY)
        counted_value = (counted * unit_price).quantize(CENT)
        difference_value = (book_value - counted_value).quantize(CENT)
        available = opening + purchased
        if available > 0:
            shrink_percent = ((closing - counted) / available * 100).quantize(CENT)
            status = ReplacementStatus.REPLACE if shrink_percent > tolerance else ReplacementStatus.TOLERATED
        else:
            status = ReplacementStatus.TOLERATED

    return StockRow(
        ingredient_id=ingredient_id,
        name=name,
        category=category,
        unit=unit,
        unit_price=unit_price,
        opening_stock=opening.quantize(QTY),
        purchased=purchased.quantize(QTY),
        used=used.quantize(QTY),
        wasted=wasted.quantize(QTY),
        rnd=rnd.quantize(QTY),
        adjustment=adjustment.quantize(QTY),
        closing_stock=closing.quantize(QTY),
        counted=counted,
        difference=difference,
        shrink_percent=shrink_percent,
        book_value=book_value,
        counted_value=counted_value,
        difference_value=difference_value,
        shrink_tolerance=tolerance,
        replacement_status=status,
    )


def stock_report(db: Session, outlet_id: str | None, start: date, end: date) -> StockReport:
    """The opening stock is the card balance before `start`, so every period begins where the previous one ended.

    Cards written by closing a count are left out of their own period, otherwise the closing stock always equals the count.
    """
    ingredients = repository.ingredients_by_category(db, outlet_id)
    openings = stock_balances.balances_before(db, outlet_id, start)
    period_movements = movements.movements_by_kind(db, outlet_id, start, end, skip_count_cards=True)

    counts = repository.counts_for_period(db, outlet_id, start, end)
    count_id = ",".join(count.id for count in counts) or None
    snapshots: dict[str, IngredientCountLine] = {}
    lines = repository.count_lines(db, [count.id for count in counts])
    for count in counts:
        for line in lines:
            if line.count_id == count.id and line.ingredient_id:
                snapshots[line.ingredient_id] = line

    rows: list[StockRow] = []
    for ingredient, category, unit in ingredients:
        opening = openings.get(ingredient.id, ZERO)
        by_kind = period_movements.get(ingredient.id, {})
        snapshot = snapshots.get(ingredient.id)
        # An inactive ingredient with no figure in the period only fills the table.
        if not ingredient.is_active and opening == 0 and not by_kind and snapshot is None:
            continue
        rows.append(
            stock_row(
                ingredient_id=ingredient.id,
                name=ingredient.name,
                category=category,
                unit=unit or "",
                unit_price=Decimal(str(snapshot.value)) if snapshot else decimal_of(ingredient.unit_price),
                tolerance=(
                    Decimal(str(snapshot.shrink_tolerance)) if snapshot else decimal_of(ingredient.shrink_tolerance)
                ),
                opening=opening,
                by_kind=by_kind,
                counted=Decimal(str(snapshot.counted)) if snapshot else None,
            )
        )

    total_replacement = total_tolerated = None
    if count_id is not None:
        total_replacement = sum(
            (row.difference_value for row in rows if row.replacement_status == ReplacementStatus.REPLACE), ZERO
        ).quantize(CENT)
        total_tolerated = sum(
            (row.difference_value for row in rows if row.replacement_status == ReplacementStatus.TOLERATED), ZERO
        ).quantize(CENT)

    return StockReport(
        start=start,
        end=end,
        count_id=count_id,
        total_replacement=total_replacement,
        total_tolerated_value=total_tolerated,
        check_count=sum(1 for row in rows if row.replacement_status == ReplacementStatus.CHECK),
        rows=rows,
    )
