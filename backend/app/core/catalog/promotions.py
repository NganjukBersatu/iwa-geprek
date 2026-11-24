"""The one door for changing a discount promo or a cafe announcement; the cashier reads them through app.core.orders.promo."""
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core import clock, uploads
from app.core.catalog import branch_scope
from app.core.errors import DomainError
from app.core.http import stored_path
from app.core.orders.promo import KIND_BASIC, KIND_PRODUCT, KIND_TOTAL, PERCENT, TYPE_NOMINAL, TYPE_PERCENT
from app.core.uploads import UploadedFile, UploadRule
from app.models.cafe_promotion import UPLOAD_FOLDER, CafePromotion
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.promo import Promo

KINDS = (KIND_BASIC, KIND_PRODUCT, KIND_TOTAL)
# "bundel" is left out: the order total has no rule for it, so it would show a promo that gives nothing.
DISCOUNT_TYPES = (TYPE_PERCENT, TYPE_NOMINAL)
ACTIVATION_AUTOMATIC = "otomatis"
ACTIVATION_MANUAL = "manual"
ACTIVATIONS = (ACTIVATION_AUTOMATIC, ACTIVATION_MANUAL)

STATUS_RUNNING = "berlaku"
STATUS_SCHEDULED = "terjadwal"
STATUS_ENDED = "berakhir"
STATUS_OFF = "nonaktif"

NOT_FOUND = 404
CONFLICT = 409

PROMO_NOT_FOUND = "Promo tidak ditemukan."
PROMO_IN_USE = "Promo ini sudah dipakai pesanan, jadi tidak bisa dihapus. Nonaktifkan agar tidak muncul di kasir dan riwayat tetap utuh."
ANNOUNCEMENT_NOT_FOUND = "Promosi tidak ditemukan."
NAME_REQUIRED = "Nama promo wajib diisi."
TITLE_REQUIRED = "Judul promosi wajib diisi."
DESCRIPTION_REQUIRED = "Deskripsi promosi wajib diisi."
KIND_UNKNOWN = "Jenis promo tidak dikenal."
TYPE_UNKNOWN = "Tipe potongan tidak dikenal."
ACTIVATION_UNKNOWN = "Cara aktivasi tidak dikenal."
VALUE_REQUIRED = "Nilai potongan harus lebih dari 0."
PERCENT_TOO_HIGH = "Potongan persen paling besar 100%."
PRODUCTS_REQUIRED = "Pilih minimal satu menu yang mendapat potongan."
PRODUCT_UNKNOWN = "Ada menu yang tidak dikenal."
MINIMUM_REQUIRED = "Isi minimal belanja untuk promo jenis total."
DATES_REVERSED = "Tanggal selesai tidak boleh sebelum tanggal mulai."
LINK_INVALID = "Tautan gambar harus diawali http:// atau https://."
PROMO_ELSEWHERE = "Promo ini berlaku untuk semua cabang. Ubah dari web admin."
ANNOUNCEMENT_ELSEWHERE = "Promosi ini berlaku untuk semua cabang. Ubah dari web admin."

LINK_PREFIXES = ("http://", "https://")


@dataclass(frozen=True)
class PromoInput:
    name: str
    description: str | None
    kind: str
    discount_type: str
    value: Decimal
    product_ids: list[str] | None
    minimum_spend: Decimal | None
    activation: str
    starts_on: date
    ends_on: date
    is_active: bool
    # Kosong berlaku di semua cabang; terisi milik satu cabang itu saja.
    outlet_id: str | None = None


@dataclass(frozen=True)
class AnnouncementInput:
    title: str
    description: str
    image_link: str | None
    starts_on: date
    ends_on: date
    is_active: bool
    outlet_id: str | None = None


def status_of(is_active: bool, starts_on: date, ends_on: date, on: date | None = None) -> str:
    day = on or clock.today()
    if not is_active:
        return STATUS_OFF
    if day < starts_on:
        return STATUS_SCHEDULED
    if day > ends_on:
        return STATUS_ENDED
    return STATUS_RUNNING


def _text(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def _check_dates(starts_on: date, ends_on: date) -> None:
    if ends_on < starts_on:
        raise DomainError(DATES_REVERSED)


# --- Discount promos ----------------------------------------------------------------


def existing_promo(db: Session, promo_id: str, outlet_scope: str | None = None) -> Promo:
    """With `outlet_scope` (a tablet) only a promo of that branch alone is returned for changing; see branch_scope.guard."""
    promo = db.get(Promo, promo_id)
    if promo is None:
        raise DomainError(PROMO_NOT_FOUND, NOT_FOUND)
    branch_scope.guard(promo.outlet_id, outlet_scope, PROMO_NOT_FOUND, PROMO_ELSEWHERE, NOT_FOUND)
    return promo


def _checked_products(db: Session, product_ids: list[str] | None) -> list[str]:
    wanted = list(dict.fromkeys(product_ids or []))
    if not wanted:
        raise DomainError(PRODUCTS_REQUIRED)
    found = set(db.scalars(select(MenuItem.id).where(MenuItem.id.in_(wanted))))
    if len(found) != len(wanted):
        raise DomainError(PRODUCT_UNKNOWN)
    return wanted


def _apply_promo(db: Session, promo: Promo, data: PromoInput) -> None:
    name = _text(data.name)
    if name is None:
        raise DomainError(NAME_REQUIRED)
    if data.kind not in KINDS:
        raise DomainError(KIND_UNKNOWN)
    if data.discount_type not in DISCOUNT_TYPES:
        raise DomainError(TYPE_UNKNOWN)
    if data.activation not in ACTIVATIONS:
        raise DomainError(ACTIVATION_UNKNOWN)
    if data.value <= 0:
        raise DomainError(VALUE_REQUIRED)
    if data.discount_type == TYPE_PERCENT and data.value > PERCENT:
        raise DomainError(PERCENT_TOO_HIGH)
    _check_dates(data.starts_on, data.ends_on)
    # A field that does not belong to the kind is cleared, so an old list never comes back when the kind changes again.
    product_ids = _checked_products(db, data.product_ids) if data.kind == KIND_PRODUCT else None
    if data.kind == KIND_TOTAL and not (data.minimum_spend and data.minimum_spend > 0):
        raise DomainError(MINIMUM_REQUIRED)
    promo.name = name
    promo.description = _text(data.description)
    promo.kind = data.kind
    promo.discount_type = data.discount_type
    promo.value = data.value
    promo.product_ids = product_ids
    promo.minimum_spend = data.minimum_spend if data.kind == KIND_TOTAL else None
    promo.activation = data.activation
    promo.starts_on = data.starts_on
    promo.ends_on = data.ends_on
    promo.is_active = data.is_active
    promo.outlet_id = branch_scope.checked(db, data.outlet_id)


def create_promo(db: Session, data: PromoInput) -> Promo:
    promo = Promo(id=str(uuid.uuid4()), applies_to=None)
    _apply_promo(db, promo, data)
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo


def input_of_promo(promo: Promo) -> PromoInput:
    """The saved promo as an input, so an edit can send only the fields it changes."""
    return PromoInput(
        name=promo.name,
        description=promo.description,
        kind=promo.kind,
        discount_type=promo.discount_type,
        value=promo.value,
        product_ids=promo.product_ids,
        minimum_spend=promo.minimum_spend,
        activation=promo.activation,
        starts_on=promo.starts_on,
        ends_on=promo.ends_on,
        is_active=promo.is_active,
        outlet_id=promo.outlet_id,
    )


def update_promo(db: Session, promo_id: str, changes: dict, outlet_scope: str | None = None) -> Promo:
    """A tablet cannot move a promo to another branch, so `outlet_id` in its changes is dropped."""
    promo = existing_promo(db, promo_id, outlet_scope)
    if outlet_scope is not None:
        changes = {key: value for key, value in changes.items() if key != "outlet_id"}
    current = input_of_promo(promo)
    merged = PromoInput(**{**current.__dict__, **{key: value for key, value in changes.items() if key in current.__dict__}})
    _apply_promo(db, promo, merged)
    db.commit()
    db.refresh(promo)
    return promo


def delete_promo(db: Session, promo_id: str, outlet_scope: str | None = None) -> None:
    """A promo no order has used is deleted for real; a used one is only switched off, so every order keeps its link."""
    promo = existing_promo(db, promo_id, outlet_scope)
    if db.scalar(select(exists().where(Order.promo_id == promo.id))):
        raise DomainError(PROMO_IN_USE, status=CONFLICT)
    db.delete(promo)
    db.commit()


# --- Cafe announcements -------------------------------------------------------------


def existing_announcement(db: Session, announcement_id: str, outlet_scope: str | None = None) -> CafePromotion:
    item = db.get(CafePromotion, announcement_id)
    if item is None:
        raise DomainError(ANNOUNCEMENT_NOT_FOUND, NOT_FOUND)
    branch_scope.guard(item.outlet_id, outlet_scope, ANNOUNCEMENT_NOT_FOUND, ANNOUNCEMENT_ELSEWHERE, NOT_FOUND)
    return item


def uploaded_path(image: str | None) -> str | None:
    """The stored file behind an image, or None when the image is a link from elsewhere."""
    stored = stored_path(image)
    return stored if stored and stored.startswith(f"{UPLOAD_FOLDER}/") else None


def _checked_link(link: str | None) -> str | None:
    cleaned = _text(link)
    if cleaned is not None and not cleaned.lower().startswith(LINK_PREFIXES):
        raise DomainError(LINK_INVALID)
    return cleaned


def _apply_announcement(db: Session, item: CafePromotion, data: AnnouncementInput, image_link: str | None, keep_image: bool) -> None:
    title = _text(data.title)
    if title is None:
        raise DomainError(TITLE_REQUIRED)
    description = _text(data.description)
    if description is None:
        raise DomainError(DESCRIPTION_REQUIRED)
    _check_dates(data.starts_on, data.ends_on)
    item.title = title
    item.description = description
    if not keep_image:
        item.image = image_link
    item.starts_on = data.starts_on
    item.ends_on = data.ends_on
    item.is_active = data.is_active
    item.outlet_id = branch_scope.checked(db, data.outlet_id)


def create_announcement(db: Session, data: AnnouncementInput) -> CafePromotion:
    item = CafePromotion(id=str(uuid.uuid4()))
    _apply_announcement(db, item, data, _checked_link(data.image_link), keep_image=False)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_announcement(db: Session, announcement_id: str, changes: dict, outlet_scope: str | None = None) -> CafePromotion:
    """`image_link` sent replaces the image, empty removes it; left out keeps the current one, uploaded or linked. A tablet cannot move it to another branch."""
    item = existing_announcement(db, announcement_id, outlet_scope)
    if outlet_scope is not None:
        changes = {key: value for key, value in changes.items() if key != "outlet_id"}
    current = AnnouncementInput(item.title, item.description, None, item.starts_on, item.ends_on, item.is_active, item.outlet_id)
    merged = AnnouncementInput(**{**current.__dict__, **{key: value for key, value in changes.items() if key in current.__dict__}})
    previous = uploaded_path(item.image)
    replacing = "image_link" in changes
    _apply_announcement(db, item, merged, _checked_link(merged.image_link) if replacing else None, keep_image=not replacing)
    db.commit()
    db.refresh(item)
    if replacing:
        uploads.discard(db, previous)
    return item


def set_announcement_image(db: Session, announcement_id: str, image: UploadedFile, rule: UploadRule) -> CafePromotion:
    item = existing_announcement(db, announcement_id)
    # A new name on every upload keeps browsers and the app from showing the old picture from cache.
    path = f"{UPLOAD_FOLDER}/{item.id}/{uuid.uuid4()}{image.extension}"
    uploads.store(db, path, image, rule)
    previous = uploaded_path(item.image)
    item.image = path
    db.commit()
    db.refresh(item)
    uploads.discard(db, previous)
    return item


def delete_announcement(db: Session, announcement_id: str, outlet_scope: str | None = None) -> None:
    item = existing_announcement(db, announcement_id, outlet_scope)
    image = uploaded_path(item.image)
    db.delete(item)
    db.commit()
    uploads.discard(db, image)
