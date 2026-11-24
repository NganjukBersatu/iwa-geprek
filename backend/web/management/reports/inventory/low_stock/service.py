"""Low stock now, for ingredients and resold items together."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.money import decimal_of
from web.management.reports.common import TENTH
from web.management.reports.inventory.constants import QTY
from web.management.reports.inventory.low_stock import repository
from web.management.reports.inventory.low_stock.domain import (
    LOW_STOCK_ORDER,
    LOW_STOCK_SOON_DAYS,
    LOW_STOCK_WINDOW_DAYS,
    LowStockItem,
    LowStockKind,
    LowStockLevel,
)

# Items without an empty-day estimate sort after every real estimate.
NO_EMPTY_ESTIMATE = Decimal("9999")


def low_stock_item(
    balance: Decimal, minimum: Decimal, daily: Decimal, **identity
) -> LowStockItem | None:
    """Out at zero, low at the minimum the owner set, soon when the recent pace empties it within two days."""
    days_left = (balance / daily).quantize(TENTH) if daily > 0 and balance > 0 else None
    if balance <= 0:
        level = LowStockLevel.OUT
    elif minimum > 0 and balance <= minimum:
        level = LowStockLevel.LOW
    elif days_left is not None and days_left <= LOW_STOCK_SOON_DAYS:
        level = LowStockLevel.SOON
    else:
        return None
    return LowStockItem(
        balance=balance,
        minimum=minimum,
        average_daily_usage=daily.quantize(QTY),
        days_until_empty=days_left,
        level=level,
        **identity,
    )


def low_stock(db: Session, outlet_id: str | None) -> list[LowStockItem]:
    """Ingredients and resold items about to run out, most urgent first."""
    window = repository.usage_window(LOW_STOCK_WINDOW_DAYS)
    items: list[LowStockItem] = []

    ingredient_usage = repository.ingredient_usage_in(db, outlet_id, window)
    for ingredient, category, unit, balance in repository.active_ingredient_balances(db, outlet_id):
        item = low_stock_item(
            decimal_of(balance),
            decimal_of(ingredient.minimum),
            decimal_of(ingredient_usage.get(ingredient.id, 0)) / LOW_STOCK_WINDOW_DAYS,
            kind=LowStockKind.INGREDIENT,
            id=ingredient.id,
            name=ingredient.name,
            category=category,
            unit=unit or "",
        )
        if item is not None:
            items.append(item)

    stock_usage = repository.stock_usage_in(db, outlet_id, window)
    for stock, menu_name, category, unit, balance in repository.tracked_stock_balances(db, outlet_id):
        item = low_stock_item(
            decimal_of(balance),
            decimal_of(stock.minimum),
            decimal_of(stock_usage.get(stock.menu_item_id, 0)) / LOW_STOCK_WINDOW_DAYS,
            kind=LowStockKind.RESALE,
            id=stock.menu_item_id,
            name=menu_name,
            category=category,
            unit=unit or "",
        )
        if item is not None:
            items.append(item)

    items.sort(
        key=lambda item: (
            LOW_STOCK_ORDER[item.level],
            item.days_until_empty if item.days_until_empty is not None else NO_EMPTY_ESTIMATE,
            item.name,
        )
    )
    return items
