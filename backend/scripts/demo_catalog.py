"""Katalog data contoh milik klien (scripts/demo_catalog.json): menu, resep, bahan, pengeluaran, dan jam sesi kas yang dipakai seed demo.

Berkas JSON-nya milik klien dan tidak ditimpa copier update, supaya data contoh setiap klien memakai menu dan bahannya sendiri.
Semua rujukan diperiksa saat dimuat, sehingga berkas yang salah ditolak dengan pesan jelas sebelum apa pun ditulis ke database.
"""
import json
from dataclasses import dataclass
from datetime import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.models.ingredient import INGREDIENT_ADJUSTMENT, INGREDIENT_IN, INGREDIENT_OUT, INGREDIENT_RND, INGREDIENT_WASTE

CATALOG_PATH = Path(__file__).resolve().parent / "demo_catalog.json"
# Gambar menu ditulis relatif terhadap akar repo, misalnya site/src/assets/images/menu.jpg.
REPO_ROOT = Path(__file__).resolve().parents[2]
UNITS = ("gram", "ml", "pcs")
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")
MOVE_KINDS = (INGREDIENT_IN, INGREDIENT_OUT, INGREDIENT_WASTE, INGREDIENT_RND, INGREDIENT_ADJUSTMENT)


class CatalogError(Exception):
    """Isi demo_catalog.json tidak sah; pesannya menyebut bagian yang salah."""


@dataclass(frozen=True)
class Menu:
    name: str
    price: Decimal
    weight: int
    image: Path | None
    recipe: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class MenuCategory:
    name: str
    menus: tuple[Menu, ...]


@dataclass(frozen=True)
class Move:
    days_ago: int
    kind: str
    qty: Decimal
    cause: str | None


@dataclass(frozen=True)
class Ingredient:
    name: str
    category: str
    unit: str
    package_price: Decimal
    package_size: Decimal
    minimum: Decimal
    shrink_tolerance: Decimal
    active: bool
    # Bahan tidak langsung (minyak, gas, kemasan) dicatat lewat pemakaian manual dan tidak pernah masuk resep.
    indirect: bool
    moves: tuple[Move, ...]


@dataclass(frozen=True)
class ExpenseItem:
    name: str
    low: int
    high: int


@dataclass(frozen=True)
class Catalog:
    branch_name: str
    opening_cash: Decimal
    shifts: tuple[tuple[time, time], ...]
    menu_categories: tuple[MenuCategory, ...]
    ingredient_categories: tuple[str, ...]
    ingredients: tuple[Ingredient, ...]
    expenses: tuple[ExpenseItem, ...]

    def menus(self) -> tuple[Menu, ...]:
        return tuple(menu for category in self.menu_categories for menu in category.menus)


def _text(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{where}: harus berupa teks yang tidak kosong")
    return value.strip()


def _number(value: object, where: str, *, allow_negative: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise CatalogError(f"{where}: harus berupa angka bulat atau teks angka")
    try:
        number = Decimal(str(value))
    except InvalidOperation as error:
        raise CatalogError(f"{where}: {value!r} bukan angka") from error
    if not number.is_finite() or (number < 0 and not allow_negative):
        raise CatalogError(f"{where}: {value!r} harus angka {'' if allow_negative else 'tidak negatif '}yang sah")
    return number


def _clock(value: object, where: str) -> time:
    try:
        return time.fromisoformat(_text(value, where))
    except ValueError as error:
        raise CatalogError(f"{where}: {value!r} bukan jam berbentuk HH:MM") from error


def _image(value: object, where: str) -> Path | None:
    if value is None:
        return None
    path = (REPO_ROOT / _text(value, where)).resolve()
    if REPO_ROOT not in path.parents:
        raise CatalogError(f"{where}: gambar harus berada di dalam repo")
    if path.suffix.lower() not in IMAGE_SUFFIXES or not path.is_file():
        raise CatalogError(f"{where}: berkas gambar {value!r} tidak ada atau bukan {', '.join(IMAGE_SUFFIXES)}")
    return path


def _ingredient(raw: dict, where: str, categories: set[str]) -> Ingredient:
    category = _text(raw.get("category"), f"{where}.category")
    if category not in categories:
        raise CatalogError(f"{where}.category: {category!r} tidak ada di ingredient_categories")
    unit = _text(raw.get("unit"), f"{where}.unit")
    if unit not in UNITS:
        raise CatalogError(f"{where}.unit: pilih salah satu dari {', '.join(UNITS)}")
    moves = []
    for index, move in enumerate(raw.get("moves", [])):
        spot = f"{where}.moves[{index}]"
        if not isinstance(move, list) or len(move) != 4:
            raise CatalogError(f"{spot}: bentuknya [hari lalu, jenis, jumlah bertanda, sebab atau null]")
        days_ago, kind, qty, cause = move
        if not isinstance(days_ago, int) or isinstance(days_ago, bool) or days_ago < 0:
            raise CatalogError(f"{spot}: hari lalu harus angka bulat tidak negatif")
        if kind not in MOVE_KINDS:
            raise CatalogError(f"{spot}: jenis harus salah satu dari {', '.join(MOVE_KINDS)}")
        moves.append(Move(days_ago, kind, _number(qty, spot, allow_negative=True), None if cause is None else _text(cause, spot)))
    package_size = _number(raw.get("package_size"), f"{where}.package_size")
    if package_size == 0:
        raise CatalogError(f"{where}.package_size: harus lebih dari nol")
    return Ingredient(
        name=_text(raw.get("name"), f"{where}.name"),
        category=category,
        unit=unit,
        package_price=_number(raw.get("package_price"), f"{where}.package_price"),
        package_size=package_size,
        minimum=_number(raw.get("minimum"), f"{where}.minimum"),
        shrink_tolerance=_number(raw.get("shrink_tolerance"), f"{where}.shrink_tolerance"),
        active=raw.get("active") is not False,
        indirect=raw.get("indirect") is True,
        moves=tuple(moves),
    )


def _menu(raw: dict, where: str, ingredients: set[str], indirect: set[str]) -> Menu:
    weight = raw.get("weight")
    if not isinstance(weight, int) or isinstance(weight, bool) or weight < 1:
        raise CatalogError(f"{where}.weight: harus angka bulat minimal 1")
    recipe = []
    for index, line in enumerate(raw.get("recipe", [])):
        spot = f"{where}.recipe[{index}]"
        if not isinstance(line, list) or len(line) != 2:
            raise CatalogError(f"{spot}: bentuknya [nama bahan, takaran]")
        name = _text(line[0], spot)
        if name not in ingredients:
            raise CatalogError(f"{spot}: bahan {name!r} tidak ada di ingredients")
        if name in indirect:
            raise CatalogError(f"{spot}: bahan tidak langsung {name!r} tidak boleh masuk resep")
        qty = _number(line[1], spot)
        if qty == 0:
            raise CatalogError(f"{spot}: takaran harus lebih dari nol")
        recipe.append((name, qty))
    if not recipe:
        raise CatalogError(f"{where}.recipe: menu tanpa resep tidak bisa dijual kasir")
    price = _number(raw.get("price"), f"{where}.price")
    if price == 0:
        raise CatalogError(f"{where}.price: harus lebih dari nol")
    return Menu(_text(raw.get("name"), f"{where}.name"), price, weight, _image(raw.get("image"), f"{where}.image"), tuple(recipe))


def _unique(names: list[str], where: str) -> None:
    seen: set[str] = set()
    for name in names:
        if name.lower() in seen:
            raise CatalogError(f"{where}: nama {name!r} dipakai lebih dari sekali")
        seen.add(name.lower())


def load(path: Path = CATALOG_PATH) -> Catalog:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise CatalogError(f"{path} tidak ada") from error
    except json.JSONDecodeError as error:
        raise CatalogError(f"{path} bukan JSON yang sah: baris {error.lineno}, kolom {error.colno}") from error
    if not isinstance(raw, dict):
        raise CatalogError(f"{path}: isinya harus satu objek JSON")

    categories = tuple(_text(name, "ingredient_categories") for name in raw.get("ingredient_categories", []))
    _unique(list(categories), "ingredient_categories")
    ingredients = tuple(_ingredient(item, f"ingredients[{index}]", set(categories)) for index, item in enumerate(raw.get("ingredients", [])))
    _unique([item.name for item in ingredients], "ingredients")
    names = {item.name for item in ingredients}
    indirect = {item.name for item in ingredients if item.indirect}
    menu_categories = tuple(
        MenuCategory(
            _text(category.get("name"), f"menu_categories[{index}].name"),
            tuple(_menu(menu, f"menu_categories[{index}].menus[{position}]", names, indirect) for position, menu in enumerate(category.get("menus", []))),
        )
        for index, category in enumerate(raw.get("menu_categories", []))
    )
    _unique([category.name for category in menu_categories], "menu_categories")
    menus = [menu.name for category in menu_categories for menu in category.menus]
    if not menus:
        raise CatalogError("menu_categories: minimal satu menu")
    _unique(menus, "menu_categories.menus")
    shifts = tuple((_clock(pair[0], f"shifts[{index}]"), _clock(pair[1], f"shifts[{index}]")) for index, pair in enumerate(raw.get("shifts", [])))
    if not shifts or any(start >= end for start, end in shifts):
        raise CatalogError("shifts: minimal satu sesi, dan jam mulai setiap sesi sebelum jam selesainya")
    expenses = tuple(
        ExpenseItem(_text(item.get("name"), f"expenses[{index}].name"), int(_number(item.get("min"), f"expenses[{index}].min")), int(_number(item.get("max"), f"expenses[{index}].max")))
        for index, item in enumerate(raw.get("expenses", []))
    )
    if any(item.low > item.high for item in expenses):
        raise CatalogError("expenses: min tidak boleh melebihi max")
    return Catalog(
        branch_name=_text(raw.get("branch_name"), "branch_name"),
        opening_cash=_number(raw.get("opening_cash"), "opening_cash"),
        shifts=shifts,
        menu_categories=menu_categories,
        ingredient_categories=categories,
        ingredients=ingredients,
        expenses=expenses,
    )
