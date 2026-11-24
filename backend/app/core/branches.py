"""Lookups about branches that more than one feature needs."""
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.outlet import Outlet


def branch_filter(column, outlet_id: str | None) -> tuple:
    """Written once so no aggregate can forget it and silently mix every branch into one figure."""
    return () if outlet_id is None else (column == outlet_id,)


def branch_ids_in_scope(db: Session, outlet_id: str | None) -> list[str]:
    """The branch asked for, or every active branch by name when none is: the one place "no branch means every branch" is read."""
    if outlet_id is not None:
        return [outlet_id]
    return list(db.scalars(select(Outlet.id).where(Outlet.is_active.is_(True)).order_by(Outlet.name)).all())


def outlets_in_scope(db: Session, outlet_id: str | None) -> list[Outlet]:
    """The same scope as branch_ids_in_scope, as rows, in one query."""
    query = select(Outlet).order_by(Outlet.name)
    query = query.where(Outlet.id == outlet_id) if outlet_id is not None else query.where(Outlet.is_active.is_(True))
    return list(db.scalars(query).all())


def outlet_name(db: Session, outlet_id: str | None) -> str | None:
    outlet = db.get(Outlet, outlet_id) if outlet_id else None
    return outlet.name if outlet is not None else None


def outlet_names(db: Session, outlet_ids: Iterable[str | None]) -> dict[str, str]:
    wanted = {outlet_id for outlet_id in outlet_ids if outlet_id}
    if not wanted:
        return {}
    return dict(db.execute(select(Outlet.id, Outlet.name).where(Outlet.id.in_(wanted))).all())
