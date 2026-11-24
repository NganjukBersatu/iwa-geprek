"""HTTP surface of the Promosi screen; every rule lives in app.core.catalog.promotions."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from pydantic import TypeAdapter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import bulk, cache, uploads
from app.core.auth import require_permission
from app.core.catalog import promotions
from app.core.catalog.promotion_schemas import (
    AnnouncementIn,
    AnnouncementOut,
    AnnouncementUpdateIn,
    PromoIn,
    PromoMenuOut,
    PromoOut,
    PromoUpdateIn,
    announcement_changes,
    announcement_out,
    promo_changes,
    promo_out,
)
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.sorting import Sort, SqlSorting
from app.core.http import public_base_url
from app.core.uploads import KIND_PHOTO, UploadRule
from app.models.cafe_promotion import CafePromotion
from app.models.menu_item import MenuItem
from app.models.promo import Promo
from app.models.user import User
from web.management.promotions.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from web.management.promotions.schemas import AnnouncementPageOut, PromoPageOut

router = APIRouter(prefix="/promotions", tags=["web-promotions"])

PERMISSION_MANAGE = "promo.kelola"

PROMOS = TypeAdapter(PromoPageOut)
PROMO_MENUS = TypeAdapter(list[PromoMenuOut])
ANNOUNCEMENTS = TypeAdapter(AnnouncementPageOut)

IMAGE_RULE = UploadRule(kinds=frozenset({KIND_PHOTO}), unreadable_note="Pilih gambar lain.", not_saved="Gambar promosi gagal disimpan. Coba lagi.")


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _menu_names(db: Session, promos: list[Promo]) -> dict[str, str]:
    """Only the menus the given promos cut, so naming them never reads the whole catalog."""
    menu_ids = {menu_id for promo in promos for menu_id in promo.product_ids or []}
    return dict(db.execute(select(MenuItem.id, MenuItem.name).where(MenuItem.id.in_(menu_ids))).all()) if menu_ids else {}


def _promo_input(body: PromoIn) -> promotions.PromoInput:
    return promotions.PromoInput(**body.model_dump())


def _announcement_input(body: AnnouncementIn) -> promotions.AnnouncementInput:
    return promotions.AnnouncementInput(**body.model_dump())


def _update_promo(db: Session, promo_id: str, body: PromoUpdateIn) -> Promo:
    return promotions.update_promo(db, promo_id, promo_changes(body))


def _update_announcement(db: Session, announcement_id: str, body: AnnouncementUpdateIn) -> CafePromotion:
    return promotions.update_announcement(db, announcement_id, announcement_changes(body))


# --- Discount promos ----------------------------------------------------------------


PROMO_SORTING = SqlSorting(
    columns={"name": Promo.name, "kind": Promo.kind, "activation": Promo.activation, "period": Promo.starts_on},
    default=(Promo.created_at.desc(),),
    tiebreak=Promo.id,
)
ANNOUNCEMENT_SORTING = SqlSorting(
    columns={"title": CafePromotion.title, "period": CafePromotion.starts_on},
    default=(CafePromotion.created_at.desc(),),
    tiebreak=CafePromotion.id,
)


@router.get("/discounts", response_model=PromoPageOut)
def list_promos(
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    """Newest first, one page at a time, so years of ended promos never load at once."""

    def build() -> PromoPageOut:
        total = db.scalar(select(func.count()).select_from(Promo)) or 0
        promos = list(db.scalars(select(Promo).order_by(*PROMO_SORTING.order_by(sort)).offset((page - 1) * size).limit(size)))
        names = _menu_names(db, promos)
        return PromoPageOut(items=[promo_out(promo, names) for promo in promos], total=total, page=page, size=size)

    return cache.read("web.promotions.discounts", (sort, page, size), build, PROMOS, cache.REFERENCE_SECONDS)


@router.get("/discounts/{promo_id}", response_model=PromoOut)
def get_promo(promo_id: str, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        promo = promotions.existing_promo(db, promo_id)
    return promo_out(promo, _menu_names(db, [promo]))


@router.post("/discounts", response_model=PromoOut, status_code=status.HTTP_201_CREATED)
def create_promo(body: PromoIn, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        promo = promotions.create_promo(db, _promo_input(body))
    return promo_out(promo, _menu_names(db, [promo]))


@router.patch("/discounts/{promo_id}", response_model=PromoOut)
def update_promo(promo_id: str, body: PromoUpdateIn, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        promo = _update_promo(db, promo_id, body)
    return promo_out(promo, _menu_names(db, [promo]))


@router.delete("/discounts/{promo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_promo(promo_id: str, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        promotions.delete_promo(db, promo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/menus", response_model=list[PromoMenuOut])
def promo_menus(db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    """Every menu by name, to choose which ones a produk promo cuts."""
    return cache.read(
        "web.promotions.menus",
        (),
        lambda: [PromoMenuOut(id=menu_id, name=name) for menu_id, name in db.execute(select(MenuItem.id, MenuItem.name).order_by(MenuItem.name)).all()],
        PROMO_MENUS,
        cache.REFERENCE_SECONDS,
    )


# --- Cafe announcements -------------------------------------------------------------


@router.get("/announcements", response_model=AnnouncementPageOut)
def list_announcements(
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    """Newest first, one page at a time."""
    base_url = public_base_url()

    def build() -> AnnouncementPageOut:
        total = db.scalar(select(func.count()).select_from(CafePromotion)) or 0
        rows = db.scalars(select(CafePromotion).order_by(*ANNOUNCEMENT_SORTING.order_by(sort)).offset((page - 1) * size).limit(size))
        return AnnouncementPageOut(items=[announcement_out(item, base_url) for item in rows], total=total, page=page, size=size)

    return cache.read("web.promotions.announcements", (base_url, sort, page, size), build, ANNOUNCEMENTS, cache.REFERENCE_SECONDS)


@router.get("/announcements/{announcement_id}", response_model=AnnouncementOut)
def get_announcement(announcement_id: str, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        item = promotions.existing_announcement(db, announcement_id)
    return announcement_out(item, public_base_url())


@router.post("/announcements", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
def create_announcement(
    body: AnnouncementIn, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))
):
    with _domain_errors():
        item = promotions.create_announcement(db, _announcement_input(body))
    return announcement_out(item, public_base_url())


@router.patch("/announcements/{announcement_id}", response_model=AnnouncementOut)
def update_announcement(
    announcement_id: str,
    body: AnnouncementUpdateIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        item = _update_announcement(db, announcement_id, body)
    return announcement_out(item, public_base_url())


@router.post("/announcements/{announcement_id}/image", response_model=AnnouncementOut)
async def replace_image(
    announcement_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        image = await uploads.receive(file, IMAGE_RULE)
        item = promotions.set_announcement_image(db, announcement_id, image, IMAGE_RULE)
    return announcement_out(item, public_base_url())


@router.delete("/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(announcement_id: str, db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        promotions.delete_announcement(db, announcement_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


discounts_bulk = APIRouter(prefix="/discounts")
announcements_bulk = APIRouter(prefix="/announcements")
bulk.add_bulk_routes(
    discounts_bulk,
    PERMISSION_MANAGE,
    create_schema=PromoIn,
    create=lambda db, body, _user, _context: promotions.create_promo(db, _promo_input(body)),
    update_schema=PromoUpdateIn,
    update=lambda db, promo_id, body, _user: _update_promo(db, promo_id, body),
    delete=lambda db, promo_id, _user: promotions.delete_promo(db, promo_id),
)
bulk.add_bulk_routes(
    announcements_bulk,
    PERMISSION_MANAGE,
    update_schema=AnnouncementUpdateIn,
    update=lambda db, announcement_id, body, _user: _update_announcement(db, announcement_id, body),
    delete=lambda db, announcement_id, _user: promotions.delete_announcement(db, announcement_id),
)
router.include_router(discounts_bulk)
router.include_router(announcements_bulk)
