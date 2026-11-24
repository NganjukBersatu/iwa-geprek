"""Database reads for the menu category screen."""
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.station import CategoryStation, Station
from web.management.menu_categories.constants import CATEGORY_KIND, MAX_CATEGORIES

Row = tuple[Category, int, str | None]


def _rows() -> Select[tuple[Category, int, str | None]]:
    used = select(MenuItem.category_id, func.count(MenuItem.id).label("total")).group_by(MenuItem.category_id).subquery()
    return (
        select(Category, func.coalesce(used.c.total, 0), Station.name)
        .outerjoin(used, used.c.category_id == Category.id)
        .outerjoin(CategoryStation, CategoryStation.category_id == Category.id)
        .outerjoin(Station, Station.id == CategoryStation.station_id)
        .where(Category.kind == CATEGORY_KIND)
    )


def listing(db: Session) -> list[Row]:
    return [(category, int(total), station) for category, total, station in db.execute(_rows().order_by(Category.name, Category.id).limit(MAX_CATEGORIES)).all()]


def detail(db: Session, category_id: str) -> Row | None:
    row = db.execute(_rows().where(Category.id == category_id)).first()
    return (row[0], int(row[1]), row[2]) if row else None


def find(db: Session, category_id: str, *, lock: bool = False) -> Category | None:
    query = select(Category).where(Category.id == category_id, Category.kind == CATEGORY_KIND)
    return db.scalar(query.with_for_update() if lock else query)


def named(db: Session, name: str) -> Category | None:
    """Names are compared without regard to case, the same as the unique index."""
    return db.scalar(select(Category).where(Category.kind == CATEGORY_KIND, Category.outlet_id.is_(None), func.lower(Category.name) == name.lower()))


def total(db: Session) -> int:
    return db.scalar(select(func.count(Category.id)).where(Category.kind == CATEGORY_KIND)) or 0


def menu_count(db: Session, category_id: str) -> int:
    return db.scalar(select(func.count(MenuItem.id)).where(MenuItem.category_id == category_id)) or 0
