"""Promos and cafe announcements on the tablet; every rule lives in app.core.catalog.promotions, picture uploads stay on the web."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.auth import require_permission
from app.core.catalog import branch_scope, promotions
from app.core.catalog.promotion_schemas import (
    AnnouncementIn,
    AnnouncementUpdateIn,
    PromoIn,
    PromoMenuOut,
    PromoUpdateIn,
    announcement_changes,
    announcement_out,
    promo_changes,
    promo_out,
)
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.http import public_base_url
from app.models.cafe_promotion import CafePromotion
from app.models.menu_item import MenuItem
from app.models.promo import Promo
from app.models.user import User
from app.operational.device import tablet_outlet_id
from app.operational.promotions.schemas import TabletAnnouncementOut, TabletPromoOut

router = APIRouter(prefix="/promotions", tags=["v2-operational-promotions"])

PERMISSION_MANAGE = "promo.kelola"


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _menu_names(db: Session) -> dict[str, str]:
    return dict(db.execute(select(MenuItem.id, MenuItem.name)).all())


def _promo(promo: Promo, names: dict[str, str], outlet_id: str) -> TabletPromoOut:
    return TabletPromoOut(**promo_out(promo, names).model_dump(), editable=branch_scope.owned_by(promo.outlet_id, outlet_id))


def _announcement(item: CafePromotion, outlet_id: str) -> TabletAnnouncementOut:
    return TabletAnnouncementOut(**announcement_out(item, public_base_url()).model_dump(), editable=branch_scope.owned_by(item.outlet_id, outlet_id))


@router.get("/discounts", response_model=list[TabletPromoOut])
def list_promos(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    """Promos for every branch and those of this branch only; another branch's promos are not shown."""
    names = _menu_names(db)
    rows = db.scalars(select(Promo).where(or_(Promo.outlet_id.is_(None), Promo.outlet_id == outlet_id)).order_by(Promo.created_at.desc()))
    return [_promo(promo, names, outlet_id) for promo in rows]


@router.post("/discounts", response_model=TabletPromoOut, status_code=status.HTTP_201_CREATED)
def create_promo(
    body: PromoIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    """A promo made on a tablet belongs to that tablet's branch, whatever the body says."""
    with _domain_errors():
        promo = promotions.create_promo(db, promotions.PromoInput(**{**body.model_dump(), "outlet_id": outlet_id}))
    return _promo(promo, _menu_names(db), outlet_id)


@router.patch("/discounts/{promo_id}", response_model=TabletPromoOut)
def update_promo(
    promo_id: str,
    body: PromoUpdateIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    with _domain_errors():
        promo = promotions.update_promo(db, promo_id, promo_changes(body), outlet_id)
    return _promo(promo, _menu_names(db), outlet_id)


@router.delete("/discounts/{promo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_promo(
    promo_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    with _domain_errors():
        promotions.delete_promo(db, promo_id, outlet_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/menus", response_model=list[PromoMenuOut])
def promo_menus(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    """The menus this branch sells by name, to choose which ones a produk promo cuts."""
    rows = db.execute(select(MenuItem.id, MenuItem.name).where(branch_scope.listed_at_clause(MenuItem.outlet_ids, outlet_id)).order_by(MenuItem.name)).all()
    return [PromoMenuOut(id=menu_id, name=name) for menu_id, name in rows]


@router.get("/announcements", response_model=list[TabletAnnouncementOut])
def list_announcements(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    rows = db.scalars(select(CafePromotion).where(or_(CafePromotion.outlet_id.is_(None), CafePromotion.outlet_id == outlet_id)).order_by(CafePromotion.created_at.desc()))
    return [_announcement(item, outlet_id) for item in rows]


@router.post("/announcements", response_model=TabletAnnouncementOut, status_code=status.HTTP_201_CREATED)
def create_announcement(
    body: AnnouncementIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    with _domain_errors():
        item = promotions.create_announcement(db, promotions.AnnouncementInput(**{**body.model_dump(), "outlet_id": outlet_id}))
    return _announcement(item, outlet_id)


@router.patch("/announcements/{announcement_id}", response_model=TabletAnnouncementOut)
def update_announcement(
    announcement_id: str,
    body: AnnouncementUpdateIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    with _domain_errors():
        item = promotions.update_announcement(db, announcement_id, announcement_changes(body), outlet_id)
    return _announcement(item, outlet_id)


@router.delete("/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    with _domain_errors():
        promotions.delete_announcement(db, announcement_id, outlet_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
