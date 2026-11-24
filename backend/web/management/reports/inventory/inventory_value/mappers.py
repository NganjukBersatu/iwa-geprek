"""Turns the inventory value into its response schema."""
from web.management.reports.inventory.inventory_value.domain import InventoryValue
from web.management.reports.inventory.inventory_value.schemas import InventoryValueOut


def inventory_value_out(value: InventoryValue) -> InventoryValueOut:
    return InventoryValueOut(**vars(value))
