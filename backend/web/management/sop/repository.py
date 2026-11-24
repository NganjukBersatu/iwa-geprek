"""Database reads for the admin's procedures and drafts."""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import ColumnElement, and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.sorting import SqlSorting
from app.models.outlet import Outlet
from app.models.role import FULL_ACCESS_ROLE_IDS, Role
from app.models.sop import Sop, SopDraft, SopRead
from app.models.user import User


def visible(db: Session, outlet_id: str | None) -> list[Sop]:
    """Every procedure, or for an account bound to one branch, the global ones and that branch's."""
    query = select(Sop)
    if outlet_id:
        query = query.where(or_(Sop.outlet_id.is_(None), Sop.outlet_id == outlet_id))
    return list(db.scalars(query.order_by(Sop.sort_order, Sop.title)).all())


def find(db: Session, sop_id: str) -> Sop | None:
    return db.get(Sop, sop_id)


def next_sort_order(db: Session) -> int:
    """A new procedure goes to the bottom of the list."""
    return int(db.scalar(select(func.coalesce(func.max(Sop.sort_order) + 1, 0))) or 0)


def outlet_names(db: Session, ids: set[str]) -> dict[str, str]:
    if not ids:
        return {}
    return dict(db.execute(select(Outlet.id, Outlet.name).where(Outlet.id.in_(ids))).all())


def drafts_of(db: Session, user_id: str) -> list[SopDraft]:
    return list(db.scalars(select(SopDraft).where(SopDraft.user_id == user_id).order_by(SopDraft.updated_at.desc())).all())


def draft_for(db: Session, user_id: str, sop_id: str) -> SopDraft | None:
    return db.scalar(select(SopDraft).where(SopDraft.user_id == user_id, SopDraft.sop_id == sop_id))


def find_draft(db: Session, draft_id: str) -> SopDraft | None:
    return db.get(SopDraft, draft_id)


@dataclass(frozen=True)
class ReaderRow:
    user_id: str
    name: str
    role_name: str | None
    outlet_name: str | None
    version: int | None
    read_at: datetime | None


def _audience(viewer_outlet_id: str | None) -> list[ColumnElement[bool]]:
    """Akun aktif yang membuka SOP di aplikasi, tanpa pemilik dan admin (mereka mengelola, bukan pembaca); akun yang terikat satu cabang hanya menghitung orang di cabangnya."""
    filters = [User.is_active.is_(True), User.deleted_at.is_(None), or_(User.role_id.is_(None), User.role_id.not_in(FULL_ACCESS_ROLE_IDS))]
    if viewer_outlet_id:
        filters.append(User.outlet_id == viewer_outlet_id)
    return filters


def _sees(sop_outlet: ColumnElement[str | None]) -> ColumnElement[bool]:
    """Sama dengan aturan baca karyawan: SOP semua cabang, SOP cabangnya sendiri, atau akun tanpa cabang yang melihat semuanya."""
    return or_(sop_outlet.is_(None), User.outlet_id.is_(None), User.outlet_id == sop_outlet)


def audience_by_outlet(db: Session, viewer_outlet_id: str | None) -> dict[str | None, int]:
    rows = db.execute(select(User.outlet_id, func.count()).where(*_audience(viewer_outlet_id)).group_by(User.outlet_id)).all()
    return {outlet_id: count for outlet_id, count in rows}


def current_read_counts(db: Session, viewer_outlet_id: str | None) -> dict[str, int]:
    """Pembaca versi terbaru per SOP dalam satu query."""
    rows = db.execute(
        select(SopRead.sop_id, func.count())
        .join(Sop, Sop.id == SopRead.sop_id)
        .join(User, User.id == SopRead.user_id)
        .where(SopRead.version >= Sop.version, _sees(Sop.outlet_id), *_audience(viewer_outlet_id))
        .group_by(SopRead.sop_id)
    ).all()
    return {sop_id: count for sop_id, count in rows}


READER_NAME = func.coalesce(func.nullif(User.name, ""), User.username)

READER_SORTING = SqlSorting(
    columns={
        "name": READER_NAME,
        "role": select(Role.name).where(Role.id == User.role_id).scalar_subquery(),
        "outlet": select(Outlet.name).where(Outlet.id == User.outlet_id).scalar_subquery(),
        "read_at": SopRead.read_at,
    },
    # Yang belum membaca versi terbaru di atas, karena merekalah yang perlu diingatkan.
    default=(func.coalesce(SopRead.version, 0).asc(), func.lower(READER_NAME)),
    tiebreak=User.id,
)


def readers_page(
    db: Session, sop: Sop, viewer_outlet_id: str | None, outlet_id: str | None, read: bool | None, sort: str | None, page: int, size: int
) -> tuple[list[ReaderRow], int, int, int]:
    """Satu halaman pembaca beserta jumlahnya: (baris, total tersaring, sudah membaca versi terbaru, seluruh pembaca di cabang yang dipilih)."""
    joined = and_(SopRead.user_id == User.id, SopRead.sop_id == sop.id)
    base = _audience(viewer_outlet_id)
    if sop.outlet_id is not None:
        base.append(or_(User.outlet_id.is_(None), User.outlet_id == sop.outlet_id))
    if outlet_id:
        base.append(User.outlet_id == outlet_id)
    current = SopRead.version >= sop.version
    # Ringkasan mengikuti cabang yang dipilih, sama dengan tabelnya; hanya filter sudah/belum membaca yang tidak ikut, supaya "x dari y" tetap utuh.
    counts = db.execute(
        select(func.count(), func.count().filter(current)).select_from(User).outerjoin(SopRead, joined).where(*base)
    ).one()
    filters = list(base)
    if read is True:
        filters.append(current)
    elif read is False:
        filters.append(or_(SopRead.version.is_(None), SopRead.version < sop.version))
    total = db.scalar(select(func.count()).select_from(User).outerjoin(SopRead, joined).where(*filters)) or 0
    rows = db.execute(
        select(
            User.id,
            READER_NAME,
            select(Role.name).where(Role.id == User.role_id).scalar_subquery(),
            select(Outlet.name).where(Outlet.id == User.outlet_id).scalar_subquery(),
            SopRead.version,
            SopRead.read_at,
        )
        .select_from(User)
        .outerjoin(SopRead, joined)
        .where(*filters)
        .order_by(*READER_SORTING.order_by(sort))
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return [ReaderRow(*row) for row in rows], total, counts[1], counts[0]
