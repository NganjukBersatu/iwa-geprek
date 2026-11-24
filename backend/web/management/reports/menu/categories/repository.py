"""Database reads of the categories report."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.core.branches import branch_filter


def sales_by_category_and_menu(db: Session, conditions: tuple) -> list:
    """(category name, menu id, menu name, qty, subtotal, known cost, lines, costed lines); the category comes from today's catalogue since lines do not keep it."""
    return db.execute(
        select(
            Category.name,
            OrderItem.menu_item_id,
            func.max(OrderItem.menu_item_name),
            func.coalesce(func.sum(OrderItem.qty), 0),
            func.coalesce(func.sum(OrderItem.subtotal), 0),
            func.coalesce(func.sum(OrderItem.qty * OrderItem.unit_cost), 0),
            func.count(OrderItem.id),
            func.count(OrderItem.unit_cost),
        )
        .select_from(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .outerjoin(MenuItem, MenuItem.id == OrderItem.menu_item_id)
        .outerjoin(Category, Category.id == MenuItem.category_id)
        .where(*conditions)
        .group_by(Category.name, OrderItem.menu_item_id)
    ).all()


def revenue_by_category(db: Session, conditions: tuple) -> list:
    """(nama kategori, menu masih ada, omzet) untuk periode pembanding, dalam satu query."""
    deleted = OrderItem.menu_item_id.is_(None)
    return list(
        db.execute(
            select(Category.name, deleted, func.coalesce(func.sum(OrderItem.subtotal), 0))
            .select_from(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .outerjoin(MenuItem, MenuItem.id == OrderItem.menu_item_id)
            .outerjoin(Category, Category.id == MenuItem.category_id)
            .where(*conditions)
            .group_by(Category.name, deleted)
        ).all()
    )


def menus_with_category(db: Session) -> list[tuple[MenuItem, str | None]]:
    """Every menu item with its category name, ordered by category then name."""
    rows = db.execute(
        select(MenuItem, Category.name)
        .outerjoin(Category, Category.id == MenuItem.category_id)
        .order_by(Category.name, MenuItem.name)
    ).all()
    return [(menu, category) for menu, category in rows]


def last_sold(db: Session, menu_ids: list[str], outlet_id: str | None) -> dict[str, datetime]:
    """Latest non-voided sale of each menu item over all time."""
    if not menu_ids:
        return {}
    return dict(
        db.execute(
            select(OrderItem.menu_item_id, func.max(Order.created_at))
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                OrderItem.menu_item_id.in_(menu_ids),
                Order.voided_at.is_(None),
                *branch_filter(Order.outlet_id, outlet_id),
            )
            .group_by(OrderItem.menu_item_id)
        ).all()
    )
