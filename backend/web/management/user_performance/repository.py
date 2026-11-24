"""Database reads for the admin's user performance."""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.search import contains
from app.models.outlet import Outlet
from app.models.user import User


def _working(outlet_id: str | None) -> list:
    filters = [User.deleted_at.is_(None), User.is_active.is_(True)]
    if outlet_id:
        filters.append(User.outlet_id == outlet_id)
    return filters


def people(db: Session, outlet_id: str | None, search: str | None) -> list[User]:
    """Akun aktif yang bekerja; jumlahnya terbatas jumlah karyawan, jadi dibaca utuh lalu diurutkan dan dipotong per halaman."""
    filters = _working(outlet_id)
    if search:
        filters.append(or_(contains(User.name, search), contains(User.username, search)))
    return list(db.scalars(select(User).where(*filters).order_by(User.username, User.id)).all())


def person(db: Session, user_id: str, outlet_id: str | None) -> User | None:
    return db.scalar(select(User).where(User.id == user_id, *_working(outlet_id)))


def outlet_names(db: Session, ids: set[str]) -> dict[str, str]:
    if not ids:
        return {}
    return dict(db.execute(select(Outlet.id, Outlet.name).where(Outlet.id.in_(ids))).all())
