"""Daftar orang untuk dipilih sebagai penyaring "Dicatat oleh": dicari dan dimuat per halaman di server, karyawan nonaktif ikut karena catatan lamanya tetap ada."""
from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.search import contains
from app.models.outlet import Outlet
from app.models.user import User


@dataclass(frozen=True)
class UserChoice:
    id: str
    name: str
    outlet_name: str | None
    is_active: bool


def page(db: Session, search: str | None, size: int, page_number: int = 1) -> list[UserChoice]:
    """Yang aktif lebih dulu lalu urut nama; cabang asal membedakan dua orang bernama sama."""
    filters = []
    if search:
        filters.append(or_(contains(User.name, search), contains(User.username, search)))
    rows = db.execute(
        select(User.id, User.name, User.username, Outlet.name, User.is_active)
        .outerjoin(Outlet, Outlet.id == User.outlet_id)
        .where(*filters)
        .order_by(User.is_active.desc(), User.name, User.username, User.id)
        .offset((page_number - 1) * size)
        .limit(size)
    ).all()
    return [UserChoice(id=id_, name=name or username, outlet_name=outlet, is_active=bool(active)) for id_, name, username, outlet, active in rows]
