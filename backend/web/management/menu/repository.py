"""Database reads for the menu screen."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.catalog.menu import CATEGORY_KIND
from app.core.search import contains
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.core.sorting import SqlSorting


SORTING = SqlSorting(
    columns={"name": MenuItem.name, "category": Category.name, "price": MenuItem.price},
    default=(Category.name, MenuItem.name),
    tiebreak=MenuItem.id,
)


def page_of(
    db: Session, search: str | None, category_id: str | None, available: bool | None, sort: str | None, page: int, size: int
) -> tuple[list[tuple[MenuItem, str | None]], int]:
    filters = []
    if search:
        filters.append(or_(contains(MenuItem.name, search), contains(Category.name, search)))
    if category_id:
        filters.append(MenuItem.category_id == category_id)
    if available is not None:
        filters.append(MenuItem.is_available.is_(available))
    joined = select(MenuItem, Category.name).outerjoin(Category, Category.id == MenuItem.category_id).where(*filters)
    total = db.scalar(select(func.count()).select_from(joined.subquery())) or 0
    rows = db.execute(joined.order_by(*SORTING.order_by(sort)).offset((page - 1) * size).limit(size)).all()
    return [(item, name) for item, name in rows], total


def with_category(db: Session, menu_id: str) -> tuple[MenuItem, str | None] | None:
    row = db.execute(
        select(MenuItem, Category.name).outerjoin(Category, Category.id == MenuItem.category_id).where(MenuItem.id == menu_id)
    ).first()
    return (row[0], row[1]) if row else None


def menu_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).where(Category.kind == CATEGORY_KIND).order_by(Category.name)).all())
