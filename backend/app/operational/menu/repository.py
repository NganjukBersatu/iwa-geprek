from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core import business_days
from app.core.catalog import branch_scope
from app.core.catalog.menu import CATEGORY_KIND
from app.core.search import contains
from app.models.category import Category
from app.models.ingredient import Ingredient, RecipeIngredient
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.stock import StockItem


def _order(sort: str | None):
    """Kategori lalu nama bila tidak memilih; nama atau waktu dibuat, naik atau turun, bila memilih."""
    if sort is None:
        return (Category.name, MenuItem.name, MenuItem.id)
    column = MenuItem.name if sort.lstrip("-") == "name" else MenuItem.created_at
    return (column.desc() if sort.startswith("-") else column.asc(), MenuItem.id)


def page_of(
    db: Session, outlet_id: str, search: str | None, category_id: str | None, page: int, size: int, sort: str | None = None
) -> tuple[list[tuple[MenuItem, str | None]], int]:
    """Only the menus this branch sells, so another branch's menus are neither listed nor counted."""
    filters = [branch_scope.listed_at_clause(MenuItem.outlet_ids, outlet_id)]
    if search:
        filters.append(or_(contains(MenuItem.name, search), contains(Category.name, search)))
    if category_id:
        filters.append(MenuItem.category_id == category_id)
    joined = select(MenuItem, Category.name).outerjoin(Category, Category.id == MenuItem.category_id).where(*filters)
    total = db.scalar(select(func.count()).select_from(joined.subquery())) or 0
    # The id breaks ties between equal names, so a menu never repeats or vanishes between pages.
    ordered = joined.order_by(*_order(sort))
    rows = db.execute(ordered.offset((page - 1) * size).limit(size)).all()
    return [(item, name) for item, name in rows], total


def category_name(db: Session, category_id: str | None) -> str | None:
    if not category_id:
        return None
    return db.scalar(select(Category.name).where(Category.id == category_id))


def menu_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).where(Category.kind == CATEGORY_KIND).order_by(Category.name)).all())


def balances(db: Session, outlet_id: str, ingredient_ids: set[str]) -> dict[str, Decimal]:
    """Stok bahan cabang saat ini; bahan cabang lain tidak ikut terbaca walau id-nya dikirim."""
    if not ingredient_ids:
        return {}
    rows = db.execute(select(Ingredient.id, Ingredient.balance).where(Ingredient.id.in_(ingredient_ids), Ingredient.outlet_id == outlet_id)).all()
    return {ingredient_id: balance for ingredient_id, balance in rows}


def sold_on(db: Session, outlet_id: str, menu_id: str, day: date) -> int:
    """Porsi menu terjual pada satu hari bisnis di cabang; pesanan yang dibatalkan tidak dihitung."""
    total = db.scalar(
        select(func.coalesce(func.sum(OrderItem.qty), 0))
        .join(Order, Order.id == OrderItem.order_id)
        .where(*business_days.valid_orders_in(day, day, outlet_id), OrderItem.menu_item_id == menu_id)
    )
    return int(total or 0)


def is_resale(db: Session, outlet_id: str, menu_id: str) -> bool:
    """Menu yang dijual sebagai barang berstok di cabang ini."""
    found = select(StockItem.menu_item_id).where(StockItem.menu_item_id == menu_id, StockItem.outlet_id == outlet_id, StockItem.is_tracked.is_(True))
    return db.scalar(found.limit(1)) is not None


def ready_ids(db: Session, outlet_id: str | None, menu_ids: list[str]) -> set[str]:
    """A menu is ready to sell where its cost is known: it has a recipe, its stock is tracked, or it has a fixed cost."""
    if not menu_ids:
        return set()
    recipes = select(RecipeIngredient.menu_item_id).where(RecipeIngredient.menu_item_id.in_(menu_ids))
    stocks = select(StockItem.menu_item_id).where(StockItem.menu_item_id.in_(menu_ids), StockItem.is_tracked.is_(True))
    fixed = select(MenuItem.id).where(MenuItem.id.in_(menu_ids), MenuItem.fixed_cost.is_not(None))
    if outlet_id:
        recipes = recipes.where(RecipeIngredient.outlet_id == outlet_id)
        stocks = stocks.where(StockItem.outlet_id == outlet_id)
    return set(db.scalars(recipes).all()) | set(db.scalars(stocks).all()) | set(db.scalars(fixed).all())
