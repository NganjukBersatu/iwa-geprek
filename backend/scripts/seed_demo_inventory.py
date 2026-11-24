"""Data demo inventori bahan untuk melihat halaman Daftar Bahan, Barang Masuk, dan Rusak & RnD; semua barisnya berawalan "demo-" supaya bisa dihapus lagi.

    python scripts/seed_demo_inventory.py           # menampilkan rencana dan menulis tidak apa pun
    python scripts/seed_demo_inventory.py --tulis   # menulis data demo setelah Anda mengetik "ya"
    python scripts/seed_demo_inventory.py --hapus   # menghapus semua data demo setelah Anda mengetik "ya"

Hanya untuk database pengembangan: ia menulis ke cabang pertama, dan database tujuannya (DATABASE_URL) ditampilkan sebelum menulis.
Butuh akun pemilik dan cabang yang dibuat lebih dulu oleh scripts/create_owner.py.
"""
import sys
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, func, select  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.exc import IntegrityError, ProgrammingError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core import money_trail  # noqa: E402
from app.core.clock import now  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.settings import settings  # noqa: E402
from app.models.category import Category, Unit  # noqa: E402
from app.models.ingredient import (  # noqa: E402
    INGREDIENT_ADJUSTMENT,
    INGREDIENT_IN,
    INGREDIENT_OUT,
    INGREDIENT_RND,
    INGREDIENT_WASTE,
    CatalogIngredient,
    Ingredient,
    IngredientCard,
)
from app.models.outlet import Outlet  # noqa: E402
from app.models.user import User  # noqa: E402

PREFIX = "demo-"
CONFIRMATION = "ya"
CATEGORY_KIND = "bahan"
UNIT_PRICE_PLACES = Decimal("0.0001")
CREATED_DAYS_AGO = 90

# Satuan yang dicari menurut nama; yang belum ada dibuat sebagai satuan demo.
UNIT_NAMES = ("gram", "ml", "pcs")
CATEGORY_NAMES = ("Susu dan Olahan", "Kopi dan Teh", "Bahan Kering", "Kemasan")

# (hari lalu, jenis, jumlah bertanda, sebab). Saldo dihitung trigger database dari jumlah semua mutasi.
Move = tuple[int, str, str, str | None]

# (nama, kategori, satuan, harga kemasan, isi kemasan, minimum, toleransi minus %, aktif, mutasi)
SPECS: tuple[tuple[str, str, str, int, int, int, int, bool, tuple[Move, ...]], ...] = (
    ("Susu Segar", "Susu dan Olahan", "ml", 18000, 1000, 5000, 3, True, (
        (40, INGREDIENT_IN, "30000", None), (30, INGREDIENT_OUT, "-9000", None), (21, INGREDIENT_IN, "20000", None),
        (12, INGREDIENT_OUT, "-14000", None), (4, INGREDIENT_OUT, "-6000", None), (3, INGREDIENT_WASTE, "-1500", "kedaluwarsa"),
    )),
    ("Krimer Kental Manis", "Susu dan Olahan", "gram", 14000, 500, 2000, 3, True, (
        (35, INGREDIENT_IN, "10000", None), (20, INGREDIENT_OUT, "-3500", None), (6, INGREDIENT_OUT, "-2800", None),
    )),
    ("Mentega", "Susu dan Olahan", "gram", 95000, 2000, 1000, 2, True, (
        (28, INGREDIENT_IN, "6000", None), (14, INGREDIENT_OUT, "-1800", None), (2, INGREDIENT_OUT, "-900", None),
    )),
    ("Keju Krim", "Susu dan Olahan", "gram", 78000, 1000, 1500, 2, True, (
        (25, INGREDIENT_IN, "4000", None), (9, INGREDIENT_OUT, "-1700", None), (1, INGREDIENT_OUT, "-1200", None),
    )),
    ("Biji Kopi Arabika", "Kopi dan Teh", "gram", 160000, 1000, 3000, 2, True, (
        (45, INGREDIENT_IN, "20000", None), (30, INGREDIENT_OUT, "-6000", None), (15, INGREDIENT_OUT, "-5500", None),
        (8, INGREDIENT_IN, "10000", None), (2, INGREDIENT_OUT, "-3000", None),
    )),
    ("Bubuk Matcha", "Kopi dan Teh", "gram", 210000, 500, 400, 3, True, (
        (30, INGREDIENT_IN, "1500", None), (10, INGREDIENT_OUT, "-600", None), (1, INGREDIENT_OUT, "-450", None),
    )),
    ("Teh Hitam", "Kopi dan Teh", "gram", 45000, 500, 300, 3, True, (
        (50, INGREDIENT_IN, "1200", None),
    )),
    ("Sirup Karamel", "Kopi dan Teh", "ml", 85000, 750, 1500, 3, True, (
        (22, INGREDIENT_IN, "3000", None), (7, INGREDIENT_OUT, "-1800", None), (1, INGREDIENT_OUT, "-900", None),
        (1, INGREDIENT_WASTE, "-350", "tumpah"),
    )),
    ("Tepung Terigu", "Bahan Kering", "gram", 13000, 1000, 5000, 3, True, (
        (33, INGREDIENT_IN, "25000", None), (18, INGREDIENT_OUT, "-8000", None), (5, INGREDIENT_OUT, "-6000", None),
    )),
    ("Gula Pasir", "Bahan Kering", "gram", 16000, 1000, 4000, 3, True, (
        (26, INGREDIENT_IN, "15000", None), (13, INGREDIENT_OUT, "-7000", None), (2, INGREDIENT_OUT, "-4200", None),
    )),
    ("Cokelat Bubuk", "Bahan Kering", "gram", 62000, 1000, 800, 3, True, (
        (20, INGREDIENT_IN, "2500", None), (11, INGREDIENT_OUT, "-900", None), (3, INGREDIENT_RND, "-250", None),
    )),
    ("Kayu Manis Bubuk", "Bahan Kering", "gram", 38000, 250, 0, 3, True, (
        (16, INGREDIENT_IN, "500", None), (4, INGREDIENT_OUT, "-120", None),
    )),
    ("Ragi Instan", "Bahan Kering", "gram", 48000, 500, 100, 3, True, (
        (24, INGREDIENT_IN, "500", None), (8, INGREDIENT_OUT, "-380", None), (1, INGREDIENT_OUT, "-100", None),
    )),
    ("Gelas Plastik 16 oz", "Kemasan", "pcs", 95000, 1000, 300, 0, True, (
        (30, INGREDIENT_IN, "2000", None), (17, INGREDIENT_OUT, "-900", None), (5, INGREDIENT_OUT, "-760", None),
    )),
    ("Sedotan Kertas", "Kemasan", "pcs", 30000, 500, 200, 0, True, (
        (19, INGREDIENT_IN, "1000", None), (6, INGREDIENT_OUT, "-1000", None),
    )),
    ("Kotak Roti", "Kemasan", "pcs", 120000, 200, 100, 0, True, (
        (14, INGREDIENT_IN, "300", None), (3, INGREDIENT_OUT, "-200", None), (1, INGREDIENT_ADJUSTMENT, "-10", None),
    )),
    ("Es Batu Kristal", "Bahan Kering", "gram", 12000, 5000, 5000, 5, False, (
        (60, INGREDIENT_IN, "10000", None), (55, INGREDIENT_OUT, "-10000", None),
    )),
)


def new_id() -> str:
    return f"{PREFIX}{uuid.uuid4()}"


def demo_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Ingredient).where(Ingredient.id.like(f"{PREFIX}%"))) or 0


def delete_demo(db: Session) -> None:
    db.execute(delete(IngredientCard).where(IngredientCard.id.like(f"{PREFIX}%")))
    db.execute(delete(Ingredient).where(Ingredient.id.like(f"{PREFIX}%")))
    db.execute(delete(CatalogIngredient).where(CatalogIngredient.id.like(f"{PREFIX}%")))
    db.execute(delete(Category).where(Category.id.like(f"{PREFIX}%")))
    db.execute(delete(Unit).where(Unit.id.like(f"{PREFIX}%")))
    db.commit()


def name_clashes(db: Session, outlet: Outlet) -> list[str]:
    """Nama bahan demo yang sudah dipakai bahan asli, supaya katalog dan cabang tidak bentrok."""
    wanted = {spec[0].lower() for spec in SPECS}
    in_catalog = set(db.scalars(select(func.lower(CatalogIngredient.name)).where(func.lower(CatalogIngredient.name).in_(wanted))))
    in_branch = set(db.scalars(select(func.lower(Ingredient.name)).where(Ingredient.outlet_id == outlet.id, func.lower(Ingredient.name).in_(wanted))))
    return sorted(in_catalog | in_branch)


def ensure_units(db: Session) -> dict[str, str]:
    """Memakai satuan yang sudah ada menurut namanya; yang belum ada dibuat sebagai satuan demo."""
    existing = {unit.name.lower(): unit.id for unit in db.scalars(select(Unit))}
    ids: dict[str, str] = {}
    for name in UNIT_NAMES:
        if name in existing:
            ids[name] = existing[name]
            continue
        unit = Unit(id=new_id(), name=name)
        db.add(unit)
        ids[name] = unit.id
    db.flush()
    return ids


def ensure_categories(db: Session) -> dict[str, str]:
    existing = {category.name.lower(): category.id for category in db.scalars(select(Category).where(Category.kind == CATEGORY_KIND))}
    ids: dict[str, str] = {}
    for name in CATEGORY_NAMES:
        if name.lower() in existing:
            ids[name] = existing[name.lower()]
            continue
        category = Category(id=new_id(), kind=CATEGORY_KIND, name=name, station=None, station_id=None)
        db.add(category)
        ids[name] = category.id
    db.flush()
    return ids


def write_all(db: Session, outlet: Outlet, owner: User) -> tuple[int, int]:
    stamp = now()
    units = ensure_units(db)
    categories = ensure_categories(db)
    ingredients = movements = 0
    for name, category, unit, price, size, minimum, tolerance, active, moves in SPECS:
        entry = CatalogIngredient(id=new_id(), name=name, unit_id=units[unit], created_at=stamp - timedelta(days=CREATED_DAYS_AGO))
        db.add(entry)
        db.flush()
        row = Ingredient(
            id=new_id(),
            outlet_id=outlet.id,
            catalog_id=entry.id,
            name=name,
            category_id=categories[category],
            unit_id=units[unit],
            photo_path=None,
            package_price=Decimal(price),
            package_size=Decimal(size),
            unit_price=(Decimal(price) / Decimal(size)).quantize(UNIT_PRICE_PLACES),
            shrink_tolerance=Decimal(tolerance),
            minimum=Decimal(minimum),
            is_active=active,
            is_available=active,
            created_at=stamp - timedelta(days=CREATED_DAYS_AGO),
            updated_at=stamp,
        )
        db.add(row)
        db.flush()
        ingredients += 1
        for days_ago, kind, qty, cause in moves:
            db.add(
                IngredientCard(
                    id=new_id(),
                    outlet_id=outlet.id,
                    ingredient_id=row.id,
                    ingredient_name=name,
                    kind=kind,
                    qty=Decimal(qty),
                    unit_price=Decimal(price) / Decimal(size) if kind == INGREDIENT_IN else None,
                    cause=cause,
                    user_id=owner.id,
                    note="Data demo" if kind in (INGREDIENT_RND, INGREDIENT_ADJUSTMENT) else None,
                    created_at=stamp - timedelta(days=days_ago),
                )
            )
            movements += 1
    db.commit()
    return ingredients, movements


def main() -> int:
    args = sys.argv[1:]
    url = make_url(settings.database_url)
    target = f"{url.host}:{url.port}/{url.database}"
    print(f"Database: {target}")

    with SessionLocal() as db:
        try:
            existing = demo_count(db)
        except ProgrammingError:
            db.rollback()
            print("Tabel belum ada di database ini. Jalankan dulu: python -m alembic upgrade head. Tidak ada yang diubah.")
            return 1

        owner = db.scalar(select(User).where(User.role_id == "owner", User.deleted_at.is_(None), User.is_active).limit(1))

        if "--hapus" in args:
            print(f"Akan menghapus data demo: {existing} bahan beserta mutasi stok, entri katalog, kategori, dan satuan demo.")
            if input(f'Ketik "{CONFIRMATION}" untuk melanjutkan: ').strip().lower() != CONFIRMATION:
                print("Dibatalkan. Tidak ada yang dihapus.")
                return 1
            if owner is not None:
                money_trail.act_as(db, owner.id)
            delete_demo(db)
            print("Selesai. Data demo dihapus.")
            return 0

        outlet = db.scalar(select(Outlet).order_by(Outlet.created_at, Outlet.id).limit(1))
        if outlet is None or owner is None:
            print("Belum ada cabang atau akun pemilik. Jalankan dulu scripts/create_owner.py --tulis. Tidak ada yang diubah.")
            return 1
        if existing:
            print(f"Sudah ada {existing} bahan demo. Hapus dulu dengan: python scripts/seed_demo_inventory.py --hapus. Tidak ada yang diubah.")
            return 1
        clashes = name_clashes(db, outlet)
        if clashes:
            print(f"Nama berikut sudah dipakai bahan asli: {', '.join(clashes)}. Tidak ada yang diubah.")
            return 1

        movement_total = sum(len(spec[-1]) for spec in SPECS)
        print(f"Cabang tujuan: {outlet.name}")
        print(f"Rencana: {len(SPECS)} bahan dalam {len(CATEGORY_NAMES)} kategori dengan {movement_total} mutasi stok (masuk, keluar, rusak, uji coba, penyesuaian).")
        if "--tulis" not in args:
            print("Belum ada yang ditulis. Jalankan dengan --tulis untuk membuatnya.")
            return 0
        if input(f'Ketik "{CONFIRMATION}" untuk menulis ke {target}: ').strip().lower() != CONFIRMATION:
            print("Dibatalkan. Tidak ada yang ditulis.")
            return 1

        try:
            money_trail.act_as(db, owner.id)
            ingredients, movements = write_all(db, outlet, owner)
        except IntegrityError as error:
            db.rollback()
            print(f"Gagal: data bertabrakan atau melanggar aturan database ({error.orig.__class__.__name__}: {error.orig}). Tidak ada yang tersimpan.")
            return 1
        print(f"Selesai. {ingredients} bahan dan {movements} mutasi stok demo ditulis.")
        print("Buka Daftar Bahan, Barang Masuk, dan Rusak & RnD di web.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
