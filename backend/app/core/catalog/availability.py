"""A menu marked out at one branch only; the menu's own switch (MenuItem.is_available) still turns it off at every branch."""
from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.menu_item import MenuOutletUnavailable


def off_ids(db: Session, outlet_id: str | None, menu_ids: Iterable[str]) -> set[str]:
    """The menus, among the given ones, that this branch has marked out; no branch means none."""
    ids = list(menu_ids)
    if not outlet_id or not ids:
        return set()
    return set(
        db.scalars(
            select(MenuOutletUnavailable.menu_item_id).where(MenuOutletUnavailable.outlet_id == outlet_id, MenuOutletUnavailable.menu_item_id.in_(ids))
        ).all()
    )


def outlets_off(db: Session, menu_ids: Iterable[str]) -> dict[str, list[str]]:
    """For each menu, the branches that marked it out, in one query; menus no branch marked are absent."""
    ids = list(menu_ids)
    if not ids:
        return {}
    result: dict[str, list[str]] = {}
    rows = db.execute(
        select(MenuOutletUnavailable.menu_item_id, MenuOutletUnavailable.outlet_id)
        .where(MenuOutletUnavailable.menu_item_id.in_(ids))
        .order_by(MenuOutletUnavailable.menu_item_id, MenuOutletUnavailable.outlet_id)
    ).all()
    for menu_id, outlet_id in rows:
        result.setdefault(menu_id, []).append(outlet_id)
    return result


def mark(db: Session, user_id: str, outlet_id: str, menu_id: str, available: bool) -> None:
    """Marks the menu out at the branch, or clears the mark; repeating either is harmless. The caller commits."""
    if available:
        db.execute(delete(MenuOutletUnavailable).where(MenuOutletUnavailable.menu_item_id == menu_id, MenuOutletUnavailable.outlet_id == outlet_id))
        return
    statement = insert(MenuOutletUnavailable).values(menu_item_id=menu_id, outlet_id=outlet_id, user_id=user_id)
    db.execute(statement.on_conflict_do_nothing(index_elements=["menu_item_id", "outlet_id"]))
