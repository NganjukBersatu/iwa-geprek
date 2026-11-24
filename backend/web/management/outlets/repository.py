"""Database reads for the branch list."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.search import contains
from app.models.outlet import Outlet


def outlets(db: Session, only_id: str | None) -> list[Outlet]:
    statement = select(Outlet).order_by(Outlet.name)
    if only_id is not None:
        statement = statement.where(Outlet.id == only_id)
    return list(db.scalars(statement).all())


def search(db: Session, only_id: str | None, text: str | None, page: int, size: int) -> tuple[list[Outlet], int]:
    """One page of branches whose name or code contains the text, by name."""
    filters = []
    if only_id is not None:
        filters.append(Outlet.id == only_id)
    if text:
        filters.append(or_(contains(Outlet.name, text), contains(Outlet.code, text)))
    total = db.scalar(select(func.count()).select_from(Outlet).where(*filters)) or 0
    rows = db.scalars(select(Outlet).where(*filters).order_by(Outlet.name, Outlet.id).offset((page - 1) * size).limit(size)).all()
    return list(rows), total
