"""HTTP surface of the order note screen: the list the tablets pick from, renamed or pruned here; every rule lives in app.core.orders.notes."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, TypeAdapter, field_validator
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import require_permission
from app.core.branches import outlet_names
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.orders import notes
from app.core.sorting import RowSorting, Sort
from app.models.user import User

router = APIRouter(prefix="/order-notes", tags=["web-order-notes"])


class OrderNoteOut(BaseModel):
    id: str
    name: str
    used_by_orders: int
    # Kosong berarti catatan umum lama yang berlaku di semua cabang.
    outlet_id: str | None
    outlet_name: str | None


class OrderNoteRenameIn(BaseModel):
    name: str = Field(min_length=1, max_length=notes.MAX_NAME_LENGTH)

    @field_validator("name", mode="before")
    @classmethod
    def _strip(cls, value):
        return value.strip() if isinstance(value, str) else value


NOTES = TypeAdapter(list[OrderNoteOut])

SORTING: RowSorting[OrderNoteOut] = RowSorting(
    keys={"name": lambda row: row.name, "outlet": lambda row: row.outlet_name or "", "used": lambda row: row.used_by_orders},
    identity=lambda row: row.id,
)


def _out(db: Session, row, used: int) -> OrderNoteOut:
    names = outlet_names(db, [row.outlet_id]) if row.outlet_id else {}
    return OrderNoteOut(id=row.id, name=row.name, used_by_orders=used, outlet_id=row.outlet_id, outlet_name=names.get(row.outlet_id) if row.outlet_id else None)


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.get("", response_model=list[OrderNoteOut])
def list_notes(sort: Sort = None, db: Session = Depends(get_db), _: User = Depends(require_permission(notes.PERMISSION_MANAGE))):
    def build() -> list[OrderNoteOut]:
        rows = notes.listed(db)
        used = notes.usage(db, [row.id for row in rows])
        names = outlet_names(db, [row.outlet_id for row in rows if row.outlet_id])
        return SORTING.apply(
            [
                OrderNoteOut(id=row.id, name=row.name, used_by_orders=used.get(row.id, 0), outlet_id=row.outlet_id, outlet_name=names.get(row.outlet_id) if row.outlet_id else None)
                for row in rows
            ],
            sort,
        )

    # Reference data; the cache drops it whenever a note or an order changes, through the tables the read touched.
    return cache.read("web.order-notes", (sort,), build, NOTES, cache.REFERENCE_SECONDS)


@router.get("/{note_id}", response_model=OrderNoteOut)
def get_note(note_id: str, db: Session = Depends(get_db), _: User = Depends(require_permission(notes.PERMISSION_MANAGE))):
    with _domain_errors():
        row = notes.get(db, note_id)
    return _out(db, row, notes.usage(db, [row.id]).get(row.id, 0))


@router.patch("/{note_id}", response_model=OrderNoteOut)
def rename_note(
    note_id: str,
    body: OrderNoteRenameIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(notes.PERMISSION_MANAGE)),
):
    with _domain_errors():
        row = notes.rename(db, note_id, body.name)
    return _out(db, row, notes.usage(db, [row.id]).get(row.id, 0))


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(notes.PERMISSION_MANAGE)),
):
    with _domain_errors():
        notes.remove(db, note_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
