"""Kategori menu yang dicetak di printer Bar dan Dapur setiap cabang; satu pintu untuk tablet dan web admin."""
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.catalog.menu import CATEGORY_KIND
from app.core.devices import printer_messages as messages
from app.core.errors import DomainError
from app.models.category import Category
from app.models.outlet import Outlet, PrintMode
from app.models.printer_category import PrinterCategory, PrinterSlot

MAX_PER_REQUEST = 200
CONFLICT = 409


@dataclass(frozen=True)
class SlotCategory:
    category_id: str
    name: str


@dataclass(frozen=True)
class PrinterSetup:
    slots: dict[PrinterSlot, list[SlotCategory]]
    # Kategori menu yang belum dipakai printer mana pun di cabang ini.
    available: list[SlotCategory]


def setup_of(db: Session, outlet_id: str) -> PrinterSetup:
    rows = db.execute(
        select(Category.id, Category.name, PrinterCategory.printer_slot)
        .outerjoin(PrinterCategory, (PrinterCategory.category_id == Category.id) & (PrinterCategory.outlet_id == outlet_id))
        .where(Category.kind == CATEGORY_KIND)
        .order_by(Category.name, Category.id)
    ).all()
    slots: dict[PrinterSlot, list[SlotCategory]] = {slot: [] for slot in PrinterSlot}
    available: list[SlotCategory] = []
    for category_id, name, slot in rows:
        entry = SlotCategory(category_id=category_id, name=name)
        if slot is None:
            available.append(entry)
        else:
            slots[PrinterSlot(slot)].append(entry)
    return PrinterSetup(slots=slots, available=available)


def _editable(db: Session, outlet_id: str) -> None:
    outlet = db.get(Outlet, outlet_id)
    if outlet is not None and outlet.print_mode == PrintMode.STATION:
        raise DomainError(messages.STATION_MODE, status=CONFLICT)


def add(db: Session, outlet_id: str, slot: PrinterSlot, category_ids: list[str], user_id: str) -> None:
    _editable(db, outlet_id)
    wanted = sorted(set(category_ids))
    if len(wanted) > MAX_PER_REQUEST:
        raise DomainError(messages.TOO_MANY.format(limit=MAX_PER_REQUEST))
    if not wanted:
        return
    found = set(db.scalars(select(Category.id).where(Category.id.in_(wanted), Category.kind == CATEGORY_KIND)).all())
    if len(found) != len(wanted):
        raise DomainError(messages.CATEGORY_NOT_FOUND, status=404)
    taken = {
        category_id: printer_slot
        for category_id, printer_slot in db.execute(
            select(PrinterCategory.category_id, PrinterCategory.printer_slot).where(
                PrinterCategory.outlet_id == outlet_id, PrinterCategory.category_id.in_(wanted)
            )
        ).all()
    }
    if any(printer_slot != slot for printer_slot in taken.values()):
        raise DomainError(messages.ALREADY_USED, status=CONFLICT)
    # Kunci utama (cabang, kategori) yang menjadi wasit bila dua layar menambah bersamaan; yang sudah ada di slot yang sama dibiarkan.
    statement = insert(PrinterCategory).values(
        [{"outlet_id": outlet_id, "category_id": category_id, "printer_slot": slot, "created_by": user_id} for category_id in wanted]
    )
    db.execute(statement.on_conflict_do_nothing(index_elements=["outlet_id", "category_id"]))
    db.flush()
    moved = db.scalar(
        select(PrinterCategory.category_id).where(
            PrinterCategory.outlet_id == outlet_id, PrinterCategory.category_id.in_(wanted), PrinterCategory.printer_slot != slot
        ).limit(1)
    )
    if moved is not None:
        raise DomainError(messages.ALREADY_USED, status=CONFLICT)


def remove(db: Session, outlet_id: str, category_id: str) -> None:
    _editable(db, outlet_id)
    db.execute(delete(PrinterCategory).where(PrinterCategory.outlet_id == outlet_id, PrinterCategory.category_id == category_id))
    db.flush()
