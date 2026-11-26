"""Catatan pesanan di tablet: dipilih dan ditambah dari kasir, diatur oleh pemegang izin kelola; semua aturan ada di app.core.orders.notes, dan tiap cabang punya daftarnya sendiri."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.auth import current_user, require_permission
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.orders import notes
from app.core.user_names import user_names
from app.models.category import Category
from app.models.device import Device
from app.models.user import User
from app.operational.device import cashier_tablet, tablet

router = APIRouter(prefix="/order-notes", tags=["v2-operational-order-notes"])

DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100
MAX_SEARCH_LENGTH = 100
MAX_ID_LENGTH = 64


class NoteIn(BaseModel):
    name: str = Field(min_length=1, max_length=notes.MAX_NAME_LENGTH)

    @field_validator("name", mode="before")
    @classmethod
    def _strip(cls, value):
        return value.strip() if isinstance(value, str) else value


class NoteOut(BaseModel):
    id: str
    name: str


class TabletOrderNoteManageOut(BaseModel):
    id: str
    name: str
    used_by_orders: int
    shared: bool = Field(description="A general note of every branch, which only the web admin can change")
    created_by: str | None = Field(description="Nama pembuatnya; kosong untuk catatan lama yang tidak tahu pembuatnya")


class TabletOrderNotePageOut(BaseModel):
    items: list[TabletOrderNoteManageOut]
    total: int
    page: int
    size: int


def _out(row: Category) -> NoteOut:
    return NoteOut(id=row.id, name=row.name)


def _managed(row: Category, used: int, names: dict[str, str]) -> TabletOrderNoteManageOut:
    return TabletOrderNoteManageOut(id=row.id, name=row.name, used_by_orders=used, shared=row.outlet_id is None, created_by=names.get(row.created_by_id or ""))


def _one_managed(db: Session, row: Category) -> TabletOrderNoteManageOut:
    return _managed(row, notes.usage(db, [row.id]).get(row.id, 0), user_names(db, [row.created_by_id]))


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.get("", response_model=list[NoteOut])
def list_notes(device: Device = Depends(cashier_tablet), db: Session = Depends(get_db), _: User = Depends(current_user)):
    """The picker of the till: the branch's own notes and the general ones."""
    return [_out(row) for row in notes.listed(db, device.outlet_id)]


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def add_note(
    body: NoteIn,
    device: Device = Depends(cashier_tablet),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(notes.PERMISSION_ADD)),
):
    """Adding a name the branch already has returns that one, so the cashier never sees a duplicate."""
    with _domain_errors():
        return _out(notes.ensure(db, body.name, device.outlet_id, user.id))


@router.get("/manage", response_model=TabletOrderNotePageOut)
def manage_notes(
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH),
    sort: str | None = Query(None, pattern="^-?name$", description="name, or -name for descending; no choice means A to Z"),
    created_by_id: str | None = Query(None, max_length=MAX_ID_LENGTH, description="Hanya catatan buatan orang ini"),
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(notes.PERMISSION_MANAGE)),
):
    """The notes to keep tidy at this branch, with how many orders carry each; never cached, so a change shows at once."""
    rows, total = notes.page_of(db, device.outlet_id, (search or "").strip() or None, sort, page, size, created_by_id)
    used = notes.usage(db, [row.id for row in rows])
    names = user_names(db, [row.created_by_id for row in rows])
    return TabletOrderNotePageOut(items=[_managed(row, used.get(row.id, 0), names) for row in rows], total=total, page=page, size=size)


@router.post("/manage", response_model=TabletOrderNoteManageOut, status_code=status.HTTP_201_CREATED)
def create_note(
    body: NoteIn,
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(notes.PERMISSION_MANAGE)),
):
    with _domain_errors():
        row = notes.ensure(db, body.name, device.outlet_id, user.id)
    return _one_managed(db, row)


@router.patch("/manage/{note_id}", response_model=TabletOrderNoteManageOut)
def rename_note(
    note_id: str,
    body: NoteIn,
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(notes.PERMISSION_MANAGE)),
):
    with _domain_errors():
        row = notes.rename(db, note_id, body.name, device.outlet_id)
    return _one_managed(db, row)


@router.delete("/manage/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: str,
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(notes.PERMISSION_MANAGE)),
):
    with _domain_errors():
        notes.remove(db, note_id, device.outlet_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
