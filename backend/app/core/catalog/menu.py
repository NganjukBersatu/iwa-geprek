"""The one door for changing a menu item: its category, branches, branch prices, photo, availability and removal."""
import uuid
from decimal import Decimal

from sqlalchemy import column, exists, select, table
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.errors import DomainError
from app.core.uploads import UploadedFile, UploadRule
from app.models.category import Category
from app.models.menu_item import MenuItem, MenuOutletPrice
from app.models.outlet import Outlet

CATEGORY_KIND = "menu"
PHOTO_FOLDER = "menu"

NOT_FOUND = 404
CONFLICT = 409

MENU_NOT_FOUND = "Menu tidak ditemukan."
NAME_REQUIRED = "Nama menu wajib diisi."
CATEGORY_REQUIRED = "Menu wajib punya kategori."
CATEGORY_NOT_FOUND = "Kategori tidak ditemukan."
BRANCH_UNKNOWN = "Cabang tidak dikenal."
BRANCHES_REQUIRED = "Pilih minimal satu cabang yang menjual menu ini."
USED_BY_PARTNER_BENEFIT = "Menu ini masih dipakai benefit karyawan mitra. Matikan menu, jangan dihapus."

# Tabel milik program mitra di backend lama; FK-nya RESTRICT, jadi diperiksa dulu supaya pengguna mendapat pesan, bukan galat database.
_partner_free_menus = table("partner_employee_free_menus", column("menu_item_id"))


def existing(db: Session, menu_id: str) -> MenuItem:
    item = db.get(MenuItem, menu_id)
    if item is None:
        raise DomainError(MENU_NOT_FOUND, status=NOT_FOUND)
    return item


def clean_name(name: str | None) -> str:
    cleaned = (name or "").strip()
    if not cleaned:
        raise DomainError(NAME_REQUIRED)
    return cleaned


def clean_description(description: str | None) -> str | None:
    return (description or "").strip() or None


def checked_category(db: Session, category_id: str | None) -> str:
    """The category decides which printer the ticket goes to, so every menu needs one of the menu kind."""
    if not category_id:
        raise DomainError(CATEGORY_REQUIRED)
    if db.scalar(select(Category.id).where(Category.id == category_id, Category.kind == CATEGORY_KIND)) is None:
        raise DomainError(CATEGORY_NOT_FOUND)
    return category_id


def _check_branches(db: Session, outlet_ids: set[str]) -> None:
    known = set(db.scalars(select(Outlet.id).where(Outlet.id.in_(list(outlet_ids)))).all())
    if outlet_ids - known:
        raise DomainError(BRANCH_UNKNOWN)


def checked_branches(db: Session, outlet_ids: list[str] | None) -> list[str] | None:
    """None sells the menu everywhere; a list limits it to those branches and may not be empty."""
    if outlet_ids is None:
        return None
    unique = sorted(set(outlet_ids))
    if not unique:
        raise DomainError(BRANCHES_REQUIRED)
    _check_branches(db, set(unique))
    return unique


def save_branch_prices(db: Session, item: MenuItem, prices: dict[str, Decimal | None] | None) -> None:
    """A figure keeps a branch price, None removes it so the branch follows the base price, and branches left out stay; does not commit."""
    if not prices:
        return
    _check_branches(db, set(prices))
    current = {row.outlet_id: row for row in db.scalars(select(MenuOutletPrice).where(MenuOutletPrice.menu_item_id == item.id)).all()}
    for outlet_id, price in prices.items():
        row = current.get(outlet_id)
        if price is None:
            if row is not None:
                db.delete(row)
        elif row is not None:
            row.price = price
        else:
            db.add(MenuOutletPrice(id=str(uuid.uuid4()), menu_item_id=item.id, outlet_id=outlet_id, price=price))


def branch_prices(db: Session, menu_ids: list[str]) -> dict[str, dict[str, Decimal]]:
    """{menu id: {branch id: price}} for the menus given, in one query."""
    if not menu_ids:
        return {}
    result: dict[str, dict[str, Decimal]] = {}
    for row in db.scalars(select(MenuOutletPrice).where(MenuOutletPrice.menu_item_id.in_(menu_ids))).all():
        result.setdefault(row.menu_item_id, {})[row.outlet_id] = row.price
    return result


def set_available(db: Session, menu_id: str, available: bool) -> MenuItem:
    item = existing(db, menu_id)
    item.is_available = available
    db.commit()
    db.refresh(item)
    return item


def set_photo(db: Session, menu_id: str, image: UploadedFile, rule: UploadRule) -> MenuItem:
    item = existing(db, menu_id)
    path = f"{PHOTO_FOLDER}/{item.id}/{uuid.uuid4()}{image.extension}"
    uploads.store(db, path, image, rule)
    previous = item.image_path
    item.image_path = path
    db.commit()
    db.refresh(item)
    uploads.discard(db, previous)
    return item


def delete(db: Session, menu_id: str) -> None:
    """Branch prices, recipes and links go with it in the database; past orders keep the copied name."""
    item = existing(db, menu_id)
    if db.scalar(select(exists().where(_partner_free_menus.c.menu_item_id == menu_id))):
        raise DomainError(USED_BY_PARTNER_BENEFIT, CONFLICT)
    photo = item.image_path
    db.delete(item)
    db.commit()
    uploads.discard(db, photo)
