"""Hapus permanen isi satu cabang: setiap baris yang menunjuk cabang itu, anak-anaknya, dan berkas fotonya.

Daftar tabel dibaca dari katalog database, jadi tabel baru yang menunjuk cabang ikut terhapus tanpa diubah di sini.
Kerja dibagi per batch dan per langkah berbatas waktu; layar memanggil langkah berikutnya sampai selesai, dan setiap langkah aman diulang.
"""
import re
import time
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import live, uploads
from app.core.errors import DomainError
from web.management.branches import messages
from web.management.branches.constants import CONFLICT

BATCH_ROWS = 500
STEP_SECONDS = 2.0
OUTLETS = "outlets"
# Akun karyawan tidak ikut terhapus; service melepasnya dari cabang dan menonaktifkannya lebih dulu.
KEPT_TABLES = frozenset({"users"})
# Perangkat dihapus paling awal supaya tablet cabang berhenti menulis selama penghapusan berjalan.
FIRST_TABLES = ("devices",)
DELETING_RULES = ("a", "r", "c")
IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


@dataclass(frozen=True)
class Part:
    table: str
    scope: str
    files: tuple[str, ...] = ()


@dataclass(frozen=True)
class Progress:
    done: bool
    finished_parts: int
    total_parts: int


# Anak yang hanya terhapus berantai dari induknya tetapi menyimpan foto atau ditahan RESTRICT (termasuk pemakaian benefit, yang menunjuk pesanan tanpa kolom cabang); dihapus lebih dulu.
LEADING_PARTS = (
    Part("benefit_usages", "order_id IN (SELECT id FROM orders WHERE outlet_id = :outlet)"),
    Part("partner_employee_free_menus", "menu_item_id IN (SELECT m.id FROM menu_items m JOIN categories k ON k.id = m.category_id WHERE k.outlet_id = :outlet)"),
    Part("menu_items", "category_id IN (SELECT id FROM categories WHERE outlet_id = :outlet)", ("image_path",)),
    Part("outlet_batch_answers", "run_id IN (SELECT r.id FROM outlet_batch_runs r JOIN outlet_batches b ON b.id = r.batch_id WHERE b.outlet_id = :outlet)", ("photo_path",)),
    Part("task_attachments", "outlet_task_id IN (SELECT id FROM outlet_tasks WHERE outlet_id = :outlet)", ("path",)),
)
# Jejak uang dihapus paling akhir: tidak punya foreign key ke cabang, dan trigger mencatat setiap order, sesi, dan pengeluaran yang terhapus ke sini.
TRAILING_PARTS = (Part("money_changes", "outlet_id = :outlet"),)
FILE_COLUMNS: dict[str, tuple[str, ...]] = {
    "attendance_records": ("clock_in_photo_path", "clock_out_photo_path"),
    "ingredients": ("photo_path",),
    "deposits": ("photo_path",),
    "expenses": ("receipt_path",),
    "ingredient_cards": ("proof_path",),
    "payment_methods": ("image_path",),
}

OWNED_SQL = text("""
SELECT k.conrelid::regclass::text AS child, a.attname AS column_name, k.confdeltype::text AS rule
FROM pg_constraint k
JOIN pg_attribute a ON a.attrelid = k.conrelid AND a.attnum = k.conkey[1]
WHERE k.contype = 'f' AND k.confrelid = 'outlets'::regclass AND array_length(k.conkey, 1) = 1
""")
EDGES_SQL = text("""
SELECT k.conrelid::regclass::text AS child, k.confrelid::regclass::text AS parent
FROM pg_constraint k
WHERE k.contype = 'f' AND k.conrelid <> k.confrelid
""")


def plan(db: Session) -> tuple[Part, ...]:
    """Urutan hapus: anak sebelum induknya, supaya RESTRICT tidak menolak dan berantai tidak menyeret batch raksasa."""
    owned = {
        row.child: Part(row.child, f"{_identifier(row.column_name)} = :outlet", FILE_COLUMNS.get(row.child, ()))
        for row in db.execute(OWNED_SQL)
        if row.rule in DELETING_RULES and row.child not in KEPT_TABLES
    }
    edges = [(row.child, row.parent) for row in db.execute(EDGES_SQL) if row.child in owned and row.parent in owned]
    return (*LEADING_PARTS, *(owned[table] for table in _children_first(owned, edges)), *TRAILING_PARTS)


def step(db: Session, outlet_id: str, parts: tuple[Part, ...]) -> Progress:
    """Menghapus sebanyak yang muat dalam satu langkah; tidak pernah meninggalkan transaksi terbuka."""
    started = time.monotonic()
    for index, part in enumerate(parts):
        while True:
            if time.monotonic() - started > STEP_SECONDS:
                return Progress(done=False, finished_parts=index, total_parts=len(parts))
            deleted, paths = _delete_batch(db, part, outlet_id)
            for path in paths:
                uploads.discard(db, path)
            if deleted < BATCH_ROWS:
                break
    return Progress(done=True, finished_parts=len(parts), total_parts=len(parts))


def changed_tables(db: Session, parts: Iterable[Part]) -> frozenset[str]:
    """Tabel yang bisa berubah karena penghapusan, termasuk anak yang terhapus berantai, untuk cache dan layar live."""
    tables = {OUTLETS, *KEPT_TABLES, *(part.table for part in parts)}
    edges = [(row.child, row.parent) for row in db.execute(EDGES_SQL)]
    grew = True
    while grew:
        reached = {child for child, parent in edges if parent in tables} - tables
        tables |= reached
        grew = bool(reached)
    return frozenset(tables)


def _delete_batch(db: Session, part: Part, outlet_id: str) -> tuple[int, list[str]]:
    table = _identifier(part.table)
    returning = ", ".join(_identifier(column) for column in part.files) or "1"
    statement = text(
        f"DELETE FROM {table} WHERE ctid = ANY(ARRAY(SELECT ctid FROM {table} WHERE {part.scope} LIMIT :limit)) RETURNING {returning}"
    )
    try:
        rows = db.execute(statement, {"outlet": outlet_id, "limit": BATCH_ROWS}).all()
        live.mark(db, (part.table,))
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise DomainError(messages.REMOVAL_BLOCKED.format(table=part.table), status=CONFLICT) from error
    paths = [value for row in rows for value in (row if part.files else ()) if value]
    return len(rows), paths


def _children_first(owned: dict[str, Part], edges: list[tuple[str, str]]) -> list[str]:
    waiting = {table: {child for child, parent in edges if parent == table} for table in owned}
    ordered: list[str] = []
    while waiting:
        ready = sorted((table for table, children in waiting.items() if not children), key=lambda table: (table not in FIRST_TABLES, table))
        if not ready:
            raise RuntimeError(f"Foreign key berputar di antara {sorted(waiting)}")
        for table in ready:
            ordered.append(table)
            del waiting[table]
        for children in waiting.values():
            children.difference_update(ready)
    return ordered


def _identifier(name: str) -> str:
    """Nama dari katalog database disisipkan ke SQL, jadi hanya bentuk nama tabel atau kolom biasa yang diterima."""
    if not IDENTIFIER.fullmatch(name):
        raise RuntimeError(f"Nama tidak wajar dari katalog: {name!r}")
    return name
