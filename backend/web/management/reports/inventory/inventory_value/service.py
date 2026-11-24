"""Inventory value now, with the dormant share."""
from sqlalchemy.orm import Session

from app.core.stock_balances import idle_days
from app.core.money import ZERO, decimal_of
from web.management.reports.common import CENT
from web.management.reports.inventory.constants import DORMANT_DAYS
from web.management.reports.inventory.inventory_value import repository
from web.management.reports.inventory.inventory_value.domain import InventoryValue


def inventory_value(db: Session, outlet_id: str | None) -> InventoryValue:
    """Money on the shelf now; an ingredient with stock and no movement for the dormant period is dormant."""
    total = ZERO
    dormant_count = 0
    dormant_value = ZERO
    for _ingredient_id, price, balance, last in repository.balances_with_last_movement(db, outlet_id):
        balance = decimal_of(balance)
        if balance <= 0:
            continue
        value = balance * decimal_of(price)
        total += value
        idle = idle_days(last)
        if idle is None or idle >= DORMANT_DAYS:
            dormant_count += 1
            dormant_value += value
    return InventoryValue(
        ingredient_stock_value=total.quantize(CENT),
        dormant_count=dormant_count,
        dormant_value=dormant_value.quantize(CENT),
    )
