"""Reads and plain writes of resold stock; no rule lives here."""
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.sorting import SqlSorting
from app.core.branches import outlets_in_scope
from app.models.category import Category, Unit
from app.models.menu_item import MenuItem
from app.models.outlet import Outlet
from app.models.user import User
from app.models.stock import StockCard, StockItem


def outlets(db: Session, outlet_id: str | None) -> list[Outlet]:
    """The branches in scope, in the order of app.core.branches."""
    return outlets_in_scope(db, outlet_id)


def items_of(db: Session, outlet_ids: list[str]) -> list[tuple[StockItem, str, str | None]]:
    """The managed items of all the branches asked for, by name; one query however many branches."""
    rows = db.execute(
        select(StockItem, MenuItem.name, Unit.name)
        .join(MenuItem, MenuItem.id == StockItem.menu_item_id)
        .outerjoin(Unit, Unit.id == StockItem.unit_id)
        .where(StockItem.outlet_id.in_(outlet_ids))
        .order_by(MenuItem.name)
    ).all()
    return [(item, name, unit) for item, name, unit in rows]


def balances(db: Session, outlet_ids: list[str]) -> dict[tuple[str, str], Decimal]:
    """Every tracked item of every branch asked for, keyed by (branch, menu)."""
    rows = db.execute(select(StockItem.outlet_id, StockItem.menu_item_id, StockItem.balance).where(StockItem.outlet_id.in_(outlet_ids)))
    return {(branch, menu_id): Decimal(str(balance)) for branch, menu_id, balance in rows}


def latest_costs(db: Session, outlet_ids: list[str]) -> dict[tuple[str, str], Decimal]:
    """The newest recorded cost of every tracked item, one index lookup each instead of ranking every card, keyed by (branch, menu)."""
    newest = (
        select(StockCard.cost_after)
        .where(StockCard.outlet_id == StockItem.outlet_id, StockCard.menu_item_id == StockItem.menu_item_id, StockCard.cost_after.is_not(None))
        .order_by(StockCard.created_at.desc(), StockCard.id.desc())
        .limit(1)
        .scalar_subquery()
    )
    rows = db.execute(select(StockItem.outlet_id, StockItem.menu_item_id, newest).where(StockItem.outlet_id.in_(outlet_ids)))
    return {(branch, menu_id): cost for branch, menu_id, cost in rows if cost is not None}


def candidates(db: Session, outlet_id: str) -> list[tuple[str, str, str | None]]:
    managed = select(StockItem.menu_item_id).where(StockItem.outlet_id == outlet_id)
    rows = db.execute(
        select(MenuItem.id, MenuItem.name, Category.name)
        .select_from(MenuItem)
        .outerjoin(Category, Category.id == MenuItem.category_id)
        .where(MenuItem.id.not_in(managed), MenuItem.fixed_cost.is_(None))
        .order_by(Category.name, MenuItem.name)
    ).all()
    return [(menu_id, name, category) for menu_id, name, category in rows]


CARD_SORTING = SqlSorting(
    columns={
        "created_at": StockCard.created_at,
        "kind": StockCard.kind,
        "qty": StockCard.qty,
        "unit_price": StockCard.unit_price,
        "user": func.coalesce(User.name, User.username),
    },
    default=(StockCard.created_at.desc(),),
    tiebreak=StockCard.id,
)


def cards_page(
    db: Session, outlet_id: str, menu_item_id: str, sort: str | None, page: int, size: int
) -> tuple[list[tuple[StockCard, str | None]], int]:
    where = (StockCard.outlet_id == outlet_id, StockCard.menu_item_id == menu_item_id)
    total = db.scalar(select(func.count()).select_from(StockCard).where(*where)) or 0
    rows = db.execute(
        select(StockCard, func.coalesce(User.name, User.username))
        .outerjoin(User, User.id == StockCard.user_id)
        .where(*where)
        .order_by(*CARD_SORTING.order_by(sort))
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return [(card, name) for card, name in rows], total


def card_with_user(db: Session, card_id: str) -> tuple[StockCard, str | None] | None:
    row = db.execute(select(StockCard, func.coalesce(User.name, User.username)).outerjoin(User, User.id == StockCard.user_id).where(StockCard.id == card_id)).first()
    return (row[0], row[1]) if row else None


def find_item(db: Session, outlet_id: str, menu_item_id: str) -> StockItem | None:
    return db.scalar(select(StockItem).where(StockItem.outlet_id == outlet_id, StockItem.menu_item_id == menu_item_id))


def find_item_by_id(db: Session, item_id: str) -> StockItem | None:
    return db.get(StockItem, item_id)


def find_menu(db: Session, menu_item_id: str) -> MenuItem | None:
    return db.get(MenuItem, menu_item_id)


def find_card(db: Session, card_id: str) -> StockCard | None:
    return db.get(StockCard, card_id)


def unit_exists(db: Session, unit_id: str) -> bool:
    return db.scalar(select(Unit.id).where(Unit.id == unit_id)) is not None


def delete_item(db: Session, item: StockItem) -> None:
    db.execute(delete(StockCard).where(StockCard.outlet_id == item.outlet_id, StockCard.menu_item_id == item.menu_item_id))
    db.delete(item)
