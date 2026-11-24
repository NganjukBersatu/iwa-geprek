"""Database reads for the branch screen."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.outlet import Outlet


def branches(db: Session, outlet_id: str | None) -> list[Outlet]:
    statement = select(Outlet)
    if outlet_id:
        statement = statement.where(Outlet.id == outlet_id)
    return list(db.scalars(statement.order_by(Outlet.is_active.desc(), Outlet.name)).all())


def find(db: Session, outlet_id: str) -> Outlet | None:
    return db.get(Outlet, outlet_id)
