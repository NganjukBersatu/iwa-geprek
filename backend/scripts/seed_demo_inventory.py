"""Data demo inventori bahan dan resep menu demo untuk melihat halaman Daftar Bahan, Barang Masuk, dan Rusak & RnD serta menjual menu demo di kasir; semua barisnya berawalan "demo-" supaya bisa dihapus lagi.

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
    INGREDIENT_RND,
    CatalogIngredient,
    Ingredient,
    IngredientCard,
    RecipeIngredient,
)
from app.models.menu_item import MenuItem  # noqa: E402
from app.models.outlet import Outlet  # noqa: E402
from app.models.user import User  # noqa: E402
from scripts import demo_catalog  # noqa: E402

PREFIX = "demo-"
CONFIRMATION = "ya"
CATEGORY_KIND = "bahan"
UNIT_PRICE_PLACES = Decimal("0.0001")
CREATED_DAYS_AGO = 90

# Bahan, kategori, mutasi stok, dan resep contoh dibaca dari demo_catalog.json milik klien; satuan yang belum ada dibuat sebagai satuan demo.
CATALOG = demo_catalog.load()


def new_id() -> str:
    return f"{PREFIX}{uuid.uuid4()}"


def demo_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Ingredient).where(Ingredient.id.like(f"{PREFIX}%"))) or 0


def delete_demo(db: Session) -> None:
    db.execute(delete(RecipeIngredient).where(RecipeIngredient.id.like(f"{PREFIX}%")))
    db.execute(delete(IngredientCard).where(IngredientCard.id.like(f"{PREFIX}%")))
    db.execute(delete(Ingredient).where(Ingredient.id.like(f"{PREFIX}%")))
    db.execute(delete(CatalogIngredient).where(CatalogIngredient.id.like(f"{PREFIX}%")))
    db.execute(delete(Category).where(Category.id.like(f"{PREFIX}%")))
    db.execute(delete(Unit).where(Unit.id.like(f"{PREFIX}%")))
    db.commit()


def name_clashes(db: Session, outlet: Outlet) -> list[str]:
    """Nama bahan demo yang sudah dipakai bahan asli, supaya katalog dan cabang tidak bentrok."""
    wanted = {item.name.lower() for item in CATALOG.ingredients}
    in_catalog = set(db.scalars(select(func.lower(CatalogIngredient.name)).where(func.lower(CatalogIngredient.name).in_(wanted))))
    in_branch = set(db.scalars(select(func.lower(Ingredient.name)).where(Ingredient.outlet_id == outlet.id, func.lower(Ingredient.name).in_(wanted))))
    return sorted(in_catalog | in_branch)


def ensure_units(db: Session) -> dict[str, str]:
    """Memakai satuan yang sudah ada menurut namanya; yang belum ada dibuat sebagai satuan demo."""
    existing = {unit.name.lower(): unit.id for unit in db.scalars(select(Unit))}
    ids: dict[str, str] = {}
    for name in sorted({item.unit for item in CATALOG.ingredients}):
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
    for name in CATALOG.ingredient_categories:
        if name.lower() in existing:
            ids[name] = existing[name.lower()]
            continue
        category = Category(id=new_id(), kind=CATEGORY_KIND, name=name, station=None, station_id=None)
        db.add(category)
        ids[name] = category.id
    db.flush()
    return ids


def write_recipes(db: Session, outlet: Outlet, ingredients: dict[str, Ingredient]) -> int:
    """Hanya menu contoh di cabang ini yang belum punya resep; menu asli dan resep yang sudah ada tidak disentuh."""
    recipes = {menu.name: menu.recipe for menu in CATALOG.menus()}
    menus = db.scalars(select(MenuItem).where(MenuItem.id.like(f"{PREFIX}%"), MenuItem.name.in_(recipes))).all()
    with_recipe = set(db.scalars(select(RecipeIngredient.menu_item_id).where(RecipeIngredient.outlet_id == outlet.id, RecipeIngredient.menu_item_id.in_([menu.id for menu in menus]))))
    lines = 0
    for menu in menus:
        if menu.id in with_recipe or outlet.id not in (menu.outlet_ids or [outlet.id]):
            continue
        for name, qty in recipes[menu.name]:
            ingredient = ingredients[name]
            db.add(RecipeIngredient(id=new_id(), outlet_id=outlet.id, menu_item_id=menu.id, ingredient_id=ingredient.id, catalog_id=ingredient.catalog_id, qty=qty))
            lines += 1
    return lines


def write_all(db: Session, outlet: Outlet, owner: User) -> tuple[int, int, int]:
    stamp = now()
    units = ensure_units(db)
    categories = ensure_categories(db)
    ingredients = movements = 0
    written: dict[str, Ingredient] = {}
    for spec in CATALOG.ingredients:
        name = spec.name
        price = spec.package_price
        size = spec.package_size
        entry = CatalogIngredient(id=new_id(), name=name, unit_id=units[spec.unit], created_at=stamp - timedelta(days=CREATED_DAYS_AGO))
        db.add(entry)
        db.flush()
        row = Ingredient(
            id=new_id(),
            outlet_id=outlet.id,
            catalog_id=entry.id,
            name=name,
            category_id=categories[spec.category],
            unit_id=units[spec.unit],
            photo_path=None,
            package_price=price,
            package_size=size,
            unit_price=(price / size).quantize(UNIT_PRICE_PLACES),
            shrink_tolerance=spec.shrink_tolerance,
            minimum=spec.minimum,
            is_active=spec.active,
            is_available=spec.active,
            is_indirect=spec.indirect,
            created_at=stamp - timedelta(days=CREATED_DAYS_AGO),
            updated_at=stamp,
        )
        db.add(row)
        db.flush()
        written[name] = row
        ingredients += 1
        for move in spec.moves:
            db.add(
                IngredientCard(
                    id=new_id(),
                    outlet_id=outlet.id,
                    ingredient_id=row.id,
                    ingredient_name=name,
                    kind=move.kind,
                    qty=move.qty,
                    unit_price=price / size if move.kind == INGREDIENT_IN else None,
                    cause=move.cause,
                    user_id=owner.id,
                    note="Data demo" if move.kind in (INGREDIENT_RND, INGREDIENT_ADJUSTMENT) else None,
                    created_at=stamp - timedelta(days=move.days_ago),
                )
            )
            movements += 1
    db.flush()
    recipe_lines = write_recipes(db, outlet, written)
    db.commit()
    return ingredients, movements, recipe_lines


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

        movement_total = sum(len(spec.moves) for spec in CATALOG.ingredients)
        print(f"Cabang tujuan: {outlet.name}")
        print(f"Rencana: {len(CATALOG.ingredients)} bahan dalam {len(CATALOG.ingredient_categories)} kategori dengan {movement_total} mutasi stok (masuk, keluar, rusak, uji coba, penyesuaian).")
        if "--tulis" not in args:
            print("Belum ada yang ditulis. Jalankan dengan --tulis untuk membuatnya.")
            return 0
        if input(f'Ketik "{CONFIRMATION}" untuk menulis ke {target}: ').strip().lower() != CONFIRMATION:
            print("Dibatalkan. Tidak ada yang ditulis.")
            return 1

        try:
            money_trail.act_as(db, owner.id)
            ingredients, movements, recipe_lines = write_all(db, outlet, owner)
        except IntegrityError as error:
            db.rollback()
            print(f"Gagal: data bertabrakan atau melanggar aturan database ({error.orig.__class__.__name__}: {error.orig}). Tidak ada yang tersimpan.")
            return 1
        print(f"Selesai. {ingredients} bahan, {movements} mutasi stok, dan {recipe_lines} baris resep menu demo ditulis.")
        print("Buka Daftar Bahan, Barang Masuk, dan Rusak & RnD di web.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
