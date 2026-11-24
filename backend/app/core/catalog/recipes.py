# Satu pintu menulis resep menu, pilihan varian, atau ekstra, dan menerapkan satu resep ke semua cabang.
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.catalog import fixed_cost
from app.core.errors import DomainError
from app.models.extra import ExtraRecipe
from app.models.ingredient import Ingredient, RecipeIngredient
from app.models.outlet import Outlet
from app.models.variant import VariantChoiceRecipe

KIND_MENU = "menu"
KIND_VARIANT = "varian"
KIND_EXTRA = "ekstra"

NOT_FOUND = 404

DUPLICATE_INGREDIENT = "Ada bahan yang disebut dua kali."
INGREDIENT_NOT_IN_BRANCH = "Ada bahan yang tidak ditemukan di cabang ini."
BRANCH_LOCKED = "Hanya akun lintas cabang yang bisa menerapkan resep ke semua cabang."


@dataclass(frozen=True)
class RecipeInput:
    ingredient_id: str
    qty: Decimal


@dataclass(frozen=True)
class CopiedIngredient:
    branch_name: str
    ingredient_name: str


@dataclass(frozen=True)
class SpreadResult:
    branches: int
    copied: list[CopiedIngredient]


def _table(kind: str):
    if kind == KIND_MENU:
        return RecipeIngredient, RecipeIngredient.menu_item_id, "menu_item_id"
    if kind == KIND_VARIANT:
        return VariantChoiceRecipe, VariantChoiceRecipe.choice_id, "choice_id"
    if kind == KIND_EXTRA:
        return ExtraRecipe, ExtraRecipe.extra_id, "extra_id"
    raise ValueError(kind)


# Tiap bahan hanya sekali dan wajib milik cabang ini.
def checked_lines(db: Session, outlet_id: str, lines: list[RecipeInput]) -> dict[str, Ingredient]:
    ids = [line.ingredient_id for line in lines]
    if len(ids) != len(set(ids)):
        raise DomainError(DUPLICATE_INGREDIENT)
    if not ids:
        return {}
    found = {row.id: row for row in db.scalars(select(Ingredient).where(Ingredient.id.in_(ids), Ingredient.outlet_id == outlet_id)).all()}
    if any(item not in found for item in ids):
        raise DomainError(INGREDIENT_NOT_IN_BRANCH, status=NOT_FOUND)
    return found


# Seluruh resep satu pemilik di satu cabang diganti sekaligus, supaya resep setengah tersimpan tidak memotong stok yang salah; tidak commit.
def replace(db: Session, kind: str, owner_id: str, outlet_id: str, lines: list[RecipeInput]) -> None:
    model, column, owner_field = _table(kind)
    if kind == KIND_MENU and lines:
        fixed_cost.ensure_no_fixed_cost(db, owner_id)
    db.execute(delete(model).where(column == owner_id, model.outlet_id == outlet_id))
    db.flush()
    if not lines:
        return
    catalog = dict(db.execute(select(Ingredient.id, Ingredient.catalog_id).where(Ingredient.id.in_([line.ingredient_id for line in lines]))).all())
    for line in lines:
        db.add(
            model(
                id=str(uuid.uuid4()),
                outlet_id=outlet_id,
                ingredient_id=line.ingredient_id,
                catalog_id=catalog.get(line.ingredient_id),
                qty=line.qty,
                **{owner_field: owner_id},
            )
        )
    db.flush()


# Bahan cabang lain dibaca dalam satu query; padanan dicari lewat katalog dulu (tahan beda ejaan), lalu nama.
class _Matches:
    def __init__(self, db: Session, outlet_ids: list[str], sources: list[Ingredient]) -> None:
        self._by_catalog: dict[tuple[str, str], Ingredient] = {}
        self._by_name: dict[tuple[str, str], Ingredient] = {}
        catalogs = {source.catalog_id for source in sources if source.catalog_id}
        names = {source.name.lower() for source in sources}
        if not outlet_ids or not sources:
            return
        rows = db.scalars(
            select(Ingredient)
            .where(Ingredient.outlet_id.in_(outlet_ids), or_(Ingredient.catalog_id.in_(catalogs), func.lower(Ingredient.name).in_(names)))
            .order_by(Ingredient.created_at, Ingredient.id)
        ).all()
        for row in rows:
            self.remember(row)

    def remember(self, row: Ingredient) -> None:
        if row.catalog_id:
            self._by_catalog.setdefault((row.outlet_id, row.catalog_id), row)
        self._by_name.setdefault((row.outlet_id, row.name.lower()), row)

    def find(self, source: Ingredient, outlet_id: str) -> Ingredient | None:
        found = self._by_catalog.get((outlet_id, source.catalog_id)) if source.catalog_id else None
        return found or self._by_name.get((outlet_id, source.name.lower()))


# Setelan mengikuti cabang sumber; nama, status aktif, foto, stok, dan riwayat tetap milik cabang itu.
def _align(target: Ingredient, source: Ingredient) -> None:
    target.category_id = source.category_id
    target.unit_id = source.unit_id
    target.package_price = source.package_price
    target.package_size = source.package_size
    target.unit_price = source.unit_price
    target.shrink_tolerance = source.shrink_tolerance
    target.minimum = source.minimum
    if source.catalog_id:
        target.catalog_id = source.catalog_id


# Salinan bahan di cabang tujuan: stok mulai 0 (saldo bawaan database) tanpa foto.
def _copy(db: Session, source: Ingredient, outlet_id: str) -> Ingredient:
    copy = Ingredient(
        id=str(uuid.uuid4()),
        outlet_id=outlet_id,
        catalog_id=source.catalog_id,
        name=source.name,
        category_id=source.category_id,
        unit_id=source.unit_id,
        photo_path=None,
        package_price=source.package_price,
        package_size=source.package_size,
        unit_price=source.unit_price,
        shrink_tolerance=source.shrink_tolerance,
        minimum=source.minimum,
        is_active=True,
        is_available=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(copy)
    db.flush()
    return copy


# Resep yang sama di setiap cabang aktif lain; bahan yang belum ada di sana langsung disalin dengan stok 0; tidak commit.
def spread(db: Session, kind: str, owner_id: str, outlet_id: str, lines: list[RecipeInput], locked_outlet_id: str | None) -> SpreadResult:
    if locked_outlet_id:
        raise DomainError(BRANCH_LOCKED)
    sources = checked_lines(db, outlet_id, lines)
    others = db.scalars(select(Outlet).where(Outlet.is_active.is_(True), Outlet.id != outlet_id).order_by(Outlet.name, Outlet.id)).all()
    matches = _Matches(db, [outlet.id for outlet in others], list(sources.values()))
    replace(db, kind, owner_id, outlet_id, lines)
    copied: list[CopiedIngredient] = []
    for outlet in others:
        branch_lines = []
        for line in lines:
            source = sources[line.ingredient_id]
            target = matches.find(source, outlet.id)
            if target is None:
                target = _copy(db, source, outlet.id)
                matches.remember(target)
                copied.append(CopiedIngredient(outlet.name, source.name))
            else:
                _align(target, source)
            branch_lines.append(RecipeInput(target.id, line.qty))
        replace(db, kind, owner_id, outlet.id, branch_lines)
    return SpreadResult(branches=1 + len(others), copied=copied)
