"""Menutup periode: hitungan fisik disimpan, lalu stok seluruh bahan cabang kembali 0."""
from datetime import date

from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.ingredients import counts
from app.core.ingredients import openings
from app.core.ingredients.counts import BookedLine
from app.models.ingredient import IngredientCard, IngredientCount, IngredientCountChange
from app.models.outlet import Outlet
from app.models.user import User
from web.management.ingredient_counts import messages, repository
from web.management.ingredient_counts.constants import NOT_FOUND
from web.management.ingredient_counts.domain import CountDraft, CountLine
from web.management.reports.inventory.ingredient_stock import service as stock


def close(db: Session, user: User, outlet_id: str, draft: CountDraft) -> IngredientCount:
    """The web sheet reads the books from the period's stock report; recording is the shared door's."""
    counts.ensure_closable(db, outlet_id, draft.start, draft.end)
    report = stock.stock_report(db, outlet_id, draft.start, draft.end)
    system = {row.ingredient_id: row for row in report.rows}
    lines = []
    for line in draft.lines:
        row = system.get(line.ingredient_id)
        if row is None:
            raise DomainError(messages.INGREDIENT_UNKNOWN, status=NOT_FOUND)
        lines.append(BookedLine(row.ingredient_id, row.name, row.closing_stock, line.counted, row.unit_price, row.shrink_tolerance))
    return counts.record(db, user, outlet_id, draft.start, draft.end, draft.note, lines)


def set_opening(db: Session, user: User, outlet_id: str, ingredient_id: str, opening, from_date) -> IngredientCard | None:
    """Stok awal dari web memakai pintu yang sama dengan tablet; bahan yang sudah sama tetap dicatat sebagai terisi."""
    if repository.find_ingredient(db, ingredient_id, outlet_id) is None:
        raise DomainError(messages.OPENING_FOR_INGREDIENT_UNKNOWN, status=NOT_FOUND)
    return openings.write(db, user, outlet_id, ingredient_id, opening, from_date)


def get(db: Session, outlet_id: str | None, count_id: str) -> IngredientCount:
    count = repository.find(db, count_id)
    if count is None or (outlet_id and count.outlet_id != outlet_id):
        raise DomainError(messages.COUNT_NOT_FOUND, status=NOT_FOUND)
    return count


def _locked(db: Session, outlet_id: str | None, count_id: str) -> IngredientCount:
    """Dua admin yang mengoreksi hitungan yang sama bergantian, supaya tiap perubahan mencatat angka yang benar-benar diganti."""
    count = get(db, outlet_id, count_id)
    db.refresh(count, with_for_update=True)
    return count


def _change(count: IngredientCount, user: User, ingredient_id: str, name: str, action: str, old, new) -> IngredientCountChange:
    return IngredientCountChange(
        outlet_id=count.outlet_id,
        count_id=count.id,
        ingredient_id=ingredient_id,
        user_id=user.id,
        period_start=count.period_start,
        period_end=count.period_end,
        ingredient_name=name,
        action=action,
        old_counted=old,
        new_counted=new,
    )


def set_lines(db: Session, user: User, outlet_id: str | None, count_id: str, lines: list[CountLine]) -> IngredientCount:
    """Mengoreksi jumlah real bahan yang dihitung saat periode ditutup; bahan yang tidak dihitung tidak bisa ditambahkan, dan stok tidak disentuh."""
    count = _locked(db, outlet_id, count_id)
    ids = [line.ingredient_id for line in lines]
    if len(set(ids)) != len(ids):
        raise DomainError(messages.DUPLICATE_INGREDIENT)
    existing = repository.lines_of(db, count.id, ids)
    if len(existing) != len(ids):
        raise DomainError(messages.NOT_COUNTED)
    for line in lines:
        current = existing[line.ingredient_id]
        if current.counted == line.counted:
            continue
        db.add(_change(count, user, current.ingredient_id, current.ingredient_name, "set", current.counted, line.counted))
        current.counted = line.counted
    db.commit()
    return count


def part_of(db: Session, outlet_id: str | None, count_id: str, start: date) -> counts.OpenPiece:
    """Bagian waktu yang ikut tertutup oleh opname ini sebagai stok awalnya; selain itu ditolak supaya halaman tidak pernah menampilkan rentang karangan."""
    count = get(db, outlet_id, count_id)
    outlet = db.get(Outlet, count.outlet_id)
    pieces = counts.absorbed_pieces(db, [outlet]).get(count.outlet_id, []) if outlet else []
    earlier = [row.period_end for row in repository.counts_before(db, count.outlet_id, count.period_start)]
    floor = max(earlier) if earlier else None
    for piece in pieces:
        if piece.start == start and piece.end is not None and piece.end < count.period_start and (floor is None or piece.start > floor):
            return piece
    raise DomainError(messages.PART_NOT_FOUND, status=NOT_FOUND)


def cancel(db: Session, outlet_id: str | None, count_id: str) -> None:
    """Undoes a closing: the balances go back and the period can be closed again with a corrected count."""
    count = get(db, outlet_id, count_id)
    repository.delete_count(db, count)
    db.commit()
