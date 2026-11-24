"""Database reads for procedures."""
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.outlet import Outlet
from app.models.sop import Sop, SopRead


def _for_branch(outlet_id: str | None):
    """Global procedures and the reader's branch; a reader without a branch sees every one."""
    return [] if outlet_id is None else [or_(Sop.outlet_id.is_(None), Sop.outlet_id == outlet_id)]


def active(db: Session, outlet_id: str | None) -> list[Sop]:
    query = select(Sop).where(Sop.active.is_(True), *_for_branch(outlet_id)).order_by(Sop.sort_order, Sop.title)
    return list(db.scalars(query).all())


def find_active(db: Session, sop_id: str, outlet_id: str | None) -> Sop | None:
    """A procedure that was switched off, or belongs to another branch, is treated as missing."""
    return db.scalar(select(Sop).where(Sop.id == sop_id, Sop.active.is_(True), *_for_branch(outlet_id)))


def outlet_names(db: Session, ids: set[str]) -> dict[str, str]:
    if not ids:
        return {}
    return dict(db.execute(select(Outlet.id, Outlet.name).where(Outlet.id.in_(ids))).all())


def reads_of(db: Session, user_id: str) -> list[SopRead]:
    return list(db.scalars(select(SopRead).where(SopRead.user_id == user_id).order_by(SopRead.sop_id)).all())


def record_read(db: Session, sop_id: str, user_id: str, version: int, at: datetime) -> SopRead:
    """Upsert; a version older than the recorded one never lowers it, so a repeated send is safe."""
    statement = insert(SopRead).values(sop_id=sop_id, user_id=user_id, version=version, read_at=at)
    statement = statement.on_conflict_do_update(
        index_elements=[SopRead.sop_id, SopRead.user_id],
        set_={"version": statement.excluded.version, "read_at": statement.excluded.read_at},
        where=SopRead.version <= statement.excluded.version,
    )
    db.execute(statement)
    query = select(SopRead).where(SopRead.sop_id == sop_id, SopRead.user_id == user_id)
    return db.scalars(query.execution_options(populate_existing=True)).one()
