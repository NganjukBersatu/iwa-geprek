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
STATIONS = ("bar", "kitchen")
# Bawaan jumlah pesanan per sesi kas bila katalog tidak menyebutnya.
DEFAULT_ORDERS_PER_SESSION = (7, 13)
PROMO_DISCOUNT_TYPES = ("persen", "nominal")
PAYMENT_CODES = ("qris", "debit", "transfer")
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
    # Nama kelompok varian dan ekstra (dari bagian variant_groups dan extras) yang ditawarkan menu ini.
    variant_groups: tuple[str, ...] = ()
    extras: tuple[str, ...] = ()


@dataclass(frozen=True)
class Choice:
    name: str
    weight: int
    recipe: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class VariantGroup:
    name: str
    required: bool
    choices: tuple[Choice, ...]


@dataclass(frozen=True)
class Extra:
    name: str
    price: Decimal
    # Peluang ekstra ini ikut pada satu baris menu yang menawarkannya, 0 sampai 1.
    rate: Decimal
    recipe: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class Promotion:
    name: str
    description: str
    discount_type: str
    value: Decimal
    minimum_spend: Decimal | None
    # Peluang promo ini dipakai pada pesanan yang memenuhi syaratnya, 0 sampai 1.
    rate: Decimal


@dataclass(frozen=True)
class Branch:
    address: str
    phone: str
    latitude: float | None
    longitude: float | None
    attendance_radius_meters: int | None
    receipt_greeting: str
    complaint_number: str
    social: tuple[tuple[str, str], ...]
    wifi: tuple[tuple[str, str], ...]
    wifi_password: str


@dataclass(frozen=True)
class MenuCategory:
    name: str
    # Stasiun yang membuat menu kategori ini di papan stasiun demo: bar atau kitchen.
    station: str
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
    orders_per_session: tuple[int, int]
    menu_categories: tuple[MenuCategory, ...]
    ingredient_categories: tuple[str, ...]
    ingredients: tuple[Ingredient, ...]
    expenses: tuple[ExpenseItem, ...]
    variant_groups: tuple[VariantGroup, ...] = ()
    extras: tuple[Extra, ...] = ()
    promotions: tuple[Promotion, ...] = ()
    branch: Branch | None = None
    # Catatan metode bayar per kode; metode yang dicatat juga diberi gambar contoh, sehingga siap dipakai kasir.
    payment_notes: tuple[tuple[str, str], ...] = ()

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


def _recipe(raw: object, where: str, ingredients: set[str], indirect: set[str], *, required: bool) -> tuple[tuple[str, Decimal], ...]:
    recipe = []
    for index, line in enumerate(raw if isinstance(raw, list) else []):
        spot = f"{where}[{index}]"
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
    if required and not recipe:
        raise CatalogError(f"{where}: menu tanpa resep tidak bisa dijual kasir")
    return tuple(recipe)


def _weight(value: object, where: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise CatalogError(f"{where}: harus angka bulat minimal 1")
    return value


def _share(value: object, where: str) -> Decimal:
    share = _number(value, where)
    if share > 1:
        raise CatalogError(f"{where}: peluang antara 0 dan 1")
    return share


def _menu(raw: dict, where: str, ingredients: set[str], indirect: set[str]) -> Menu:
    weight = _weight(raw.get("weight"), f"{where}.weight")
    recipe = _recipe(raw.get("recipe", []), f"{where}.recipe", ingredients, indirect, required=True)
    price = _number(raw.get("price"), f"{where}.price")
    if price == 0:
        raise CatalogError(f"{where}.price: harus lebih dari nol")
    groups = tuple(_text(name, f"{where}.variant_groups") for name in raw.get("variant_groups", []))
    extras = tuple(_text(name, f"{where}.extras") for name in raw.get("extras", []))
    return Menu(_text(raw.get("name"), f"{where}.name"), price, weight, _image(raw.get("image"), f"{where}.image"), recipe, groups, extras)


def _variant_group(raw: dict, where: str, ingredients: set[str], indirect: set[str]) -> VariantGroup:
    choices = tuple(
        Choice(
            _text(choice.get("name"), f"{where}.choices[{index}].name"),
            _weight(choice.get("weight", 1), f"{where}.choices[{index}].weight"),
            _recipe(choice.get("recipe", []), f"{where}.choices[{index}].recipe", ingredients, indirect, required=False),
        )
        for index, choice in enumerate(raw.get("choices", []))
    )
    if not choices:
        raise CatalogError(f"{where}.choices: minimal satu pilihan")
    _unique([choice.name for choice in choices], f"{where}.choices")
    return VariantGroup(_text(raw.get("name"), f"{where}.name"), raw.get("required") is True, choices)


def _extra(raw: dict, where: str, ingredients: set[str], indirect: set[str]) -> Extra:
    return Extra(
        _text(raw.get("name"), f"{where}.name"),
        _number(raw.get("price"), f"{where}.price"),
        _share(raw.get("rate", 0), f"{where}.rate"),
        _recipe(raw.get("recipe", []), f"{where}.recipe", ingredients, indirect, required=False),
    )


def _promotion(raw: dict, where: str) -> Promotion:
    discount_type = raw.get("discount_type")
    if discount_type not in PROMO_DISCOUNT_TYPES:
        raise CatalogError(f"{where}.discount_type: pilih salah satu dari {', '.join(PROMO_DISCOUNT_TYPES)}")
    value = _number(raw.get("value"), f"{where}.value")
    if value == 0 or (discount_type == "persen" and value > 100):
        raise CatalogError(f"{where}.value: lebih dari nol, dan paling banyak 100 untuk persen")
    minimum = raw.get("minimum_spend")
    return Promotion(
        _text(raw.get("name"), f"{where}.name"),
        _text(raw.get("description"), f"{where}.description"),
        str(discount_type),
        value,
        None if minimum is None else _number(minimum, f"{where}.minimum_spend"),
        _share(raw.get("rate", 0), f"{where}.rate"),
    )


def _pairs(raw: object, where: str, first: str, second: str) -> tuple[tuple[str, str], ...]:
    items = raw if isinstance(raw, list) else []
    return tuple((_text(item.get(first), f"{where}[{index}].{first}"), _text(item.get(second), f"{where}[{index}].{second}")) for index, item in enumerate(items))


def _branch(raw: object) -> Branch | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise CatalogError("branch: harus berupa objek")
    latitude, longitude = raw.get("latitude"), raw.get("longitude")
    if (latitude is None) != (longitude is None):
        raise CatalogError("branch: latitude dan longitude diisi berdua atau dikosongkan berdua")
    located = latitude is not None
    if located and not (isinstance(latitude, (int, float)) and isinstance(longitude, (int, float)) and -90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise CatalogError("branch: latitude atau longitude di luar batas")
    radius = raw.get("attendance_radius_meters")
    if radius is not None and (not isinstance(radius, int) or isinstance(radius, bool) or radius < 1):
        raise CatalogError("branch.attendance_radius_meters: angka bulat minimal 1")
    return Branch(
        address=str(raw.get("address", "")).strip(),
        phone=str(raw.get("phone", "")).strip(),
        latitude=float(latitude) if located else None,
        longitude=float(longitude) if located else None,
        attendance_radius_meters=radius,
        receipt_greeting=str(raw.get("receipt_greeting", "")).strip(),
        complaint_number=str(raw.get("complaint_number", "")).strip(),
        social=_pairs(raw.get("social"), "branch.social", "icon", "handle"),
        wifi=_pairs(raw.get("wifi"), "branch.wifi", "area", "ssid"),
        wifi_password=str(raw.get("wifi_password", "")).strip(),
    )


def _station(value: object, where: str) -> str:
    if value not in STATIONS:
        raise CatalogError(f"{where}: pilih salah satu dari {', '.join(STATIONS)}")
    return str(value)


def _range(value: object, where: str) -> tuple[int, int]:
    if value is None:
        return DEFAULT_ORDERS_PER_SESSION
    valid = isinstance(value, list) and len(value) == 2 and all(isinstance(item, int) and not isinstance(item, bool) for item in value)
    if not valid or not 1 <= value[0] <= value[1] <= 500:
        raise CatalogError(f"{where}: bentuknya [paling sedikit, paling banyak], antara 1 dan 500")
    return value[0], value[1]


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
            _station(category.get("station", "kitchen"), f"menu_categories[{index}].station"),
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
    variant_groups = tuple(_variant_group(item, f"variant_groups[{index}]", names, indirect) for index, item in enumerate(raw.get("variant_groups", [])))
    _unique([group.name for group in variant_groups], "variant_groups")
    extras = tuple(_extra(item, f"extras[{index}]", names, indirect) for index, item in enumerate(raw.get("extras", [])))
    _unique([extra.name for extra in extras], "extras")
    group_names = {group.name for group in variant_groups}
    extra_names = {extra.name for extra in extras}
    for category in menu_categories:
        for menu in category.menus:
            unknown = [name for name in menu.variant_groups if name not in group_names] + [name for name in menu.extras if name not in extra_names]
            if unknown:
                raise CatalogError(f"{menu.name}: varian atau ekstra {', '.join(unknown)} tidak ada di variant_groups atau extras")
    promotions = tuple(_promotion(item, f"promotions[{index}]") for index, item in enumerate(raw.get("promotions", [])))
    notes = raw.get("payment_notes", {})
    if not isinstance(notes, dict) or any(code not in PAYMENT_CODES for code in notes):
        raise CatalogError(f"payment_notes: objek dengan kunci {', '.join(PAYMENT_CODES)}")
    return Catalog(
        variant_groups=variant_groups,
        extras=extras,
        promotions=promotions,
        branch=_branch(raw.get("branch")),
        payment_notes=tuple((code, _text(note, f"payment_notes.{code}")) for code, note in notes.items()),
        branch_name=_text(raw.get("branch_name"), "branch_name"),
        opening_cash=_number(raw.get("opening_cash"), "opening_cash"),
        shifts=shifts,
        orders_per_session=_range(raw.get("orders_per_session"), "orders_per_session"),
        menu_categories=menu_categories,
        ingredient_categories=categories,
        ingredients=ingredients,
        expenses=expenses,
    )
