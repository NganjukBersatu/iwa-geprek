"""Turns menu items into their response schema."""
from decimal import Decimal

from app.core.http import static_url
from app.models.category import Category
from app.models.menu_item import MenuItem
from web.management.menu.schemas import MenuCategoryOut, MenuItemOut


def menu_out(item: MenuItem, category_name: str | None, branch_prices: dict[str, Decimal], unavailable_outlet_ids: list[str], base_url: str) -> MenuItemOut:
    return MenuItemOut(
        id=item.id,
        name=item.name,
        description=item.description,
        price=item.price,
        category_id=item.category_id,
        category_name=category_name,
        image_url=static_url(base_url, item.image_path),
        is_available=item.is_available,
        unavailable_outlet_ids=unavailable_outlet_ids,
        outlet_ids=item.outlet_ids,
        branch_prices=branch_prices,
        tax_percent=item.tax_percent,
        service_percent=item.service_percent,
        has_fixed_cost=item.fixed_cost is not None,
    )


def category_out(category: Category) -> MenuCategoryOut:
    return MenuCategoryOut(id=category.id, name=category.name)
