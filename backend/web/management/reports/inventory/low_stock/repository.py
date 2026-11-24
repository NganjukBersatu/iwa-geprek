"""Database reads of the low stock report; every aggregate covers all items in one query."""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session

from app.core.business_days import within
from app.core.clock import today
from app.models.category import Category, Unit
from app.models.ingredient import INGREDIENT_OUT, INGREDIENT_RND, INGREDIENT_WASTE, Ingredient, IngredientCard
from app.models.menu_item import MenuItem
from app.models.stock import STOCK_OUT, StockCard, StockItem
from app.core.branches import branch_filter

USAGE_KINDS = (INGREDIENT_OUT, INGREDIENT_WASTE, INGREDIENT_RND)


def active_ingredient_balances(db: Session, outlet_id: str | None) -> list[Row]:
    """(ingredient, category name, unit name, balance) of every active ingredient."""
    return list(
        db.execute(
            select(Ingredient, Category.name, Unit.name, Ingredient.balance)
            .outerjoin(Category, Category.id == Ingredient.category_id)
            .outerjoin(Unit, Unit.id == Ingredient.unit_id)
            .where(Ingredient.is_active.is_(True), *branch_filter(Ingredient.outlet_id, outlet_id))
        ).all()
    )


def usage_window(days: int) -> tuple[date, date]:
    """The last whole business days before today, so a day still running never lowers the pace."""
    current = today()
    return current - timedelta(days=days), current - timedelta(days=1)


def ingredient_usage_in(db: Session, outlet_id: str | None, window: tuple[date, date]) -> dict[str, Decimal]:
    """Positive quantity used, wasted, or spent on R&D on the business days of the window."""
    return dict(
        db.execute(
            select(IngredientCard.ingredient_id, func.coalesce(func.sum(-IngredientCard.qty), 0))
            .where(
                *within(IngredientCard.business_day, *window),
                IngredientCard.kind.in_(USAGE_KINDS),
                *branch_filter(IngredientCard.outlet_id, outlet_id),
            )
            .group_by(IngredientCard.ingredient_id)
        ).all()
    )


def tracked_stock_balances(db: Session, outlet_id: str | None) -> list[Row]:
    """(stock item, menu name, category name, unit name, balance) of every tracked resold item."""
    return list(
        db.execute(
            select(StockItem, MenuItem.name, Category.name, Unit.name, StockItem.balance)
            .join(MenuItem, MenuItem.id == StockItem.menu_item_id)
            .outerjoin(Category, Category.id == MenuItem.category_id)
            .outerjoin(Unit, Unit.id == StockItem.unit_id)
            .where(StockItem.is_tracked.is_(True), *branch_filter(StockItem.outlet_id, outlet_id))
        ).all()
    )


def stock_usage_in(db: Session, outlet_id: str | None, window: tuple[date, date]) -> dict[str, Decimal]:
    """Positive quantity sold on the business days of the window, per menu item."""
    return dict(
        db.execute(
            select(StockCard.menu_item_id, func.coalesce(func.sum(-StockCard.qty), 0))
            .where(
                *within(StockCard.business_day, *window),
                StockCard.kind == STOCK_OUT,
                *branch_filter(StockCard.outlet_id, outlet_id),
            )
            .group_by(StockCard.menu_item_id)
        ).all()
    )
