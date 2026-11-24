"""A menu's fixed cost: the amounts need the cost permission on top of the menu one, every change is logged, and nothing here is cached because only cost viewers read it, rarely."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.auth import require_permission
from app.core.catalog import fixed_cost
from app.core.catalog import menu as catalog_menu
from app.core.catalog.recipe_book import PERMISSION_COST
from app.core.database import get_db
from app.core.errors import DomainError
from app.models.user import User
from web.management.menu.schemas import FixedCostIn, FixedCostOut

log = logging.getLogger("cafe.menu")

router = APIRouter(prefix="/menu", tags=["web-menu-cost"])

PERMISSION_MANAGE = "menu.kelola"

BRANCH_LOCKED_BASE = "Akun yang terikat satu cabang hanya boleh mengatur harga pokok cabangnya sendiri."
BRANCH_LOCKED_OTHER = "Akun yang terikat satu cabang tidak boleh mengatur harga pokok cabang lain."


def _read(db: Session, menu_id: str) -> FixedCostOut:
    item = catalog_menu.existing(db, menu_id)
    costs = fixed_cost.branch_costs(db, [item.id]).get(item.id, {}) if item.fixed_cost is not None else {}
    return FixedCostOut(cost=item.fixed_cost, branch_costs=costs)


def _branch_scope(user: User, body: FixedCostIn) -> None:
    """An account bound to a branch may only touch its own branch's figure, never the base every branch follows."""
    if not user.locked_outlet_id:
        return
    if body.cost is not None:
        raise DomainError(BRANCH_LOCKED_BASE, status=status.HTTP_403_FORBIDDEN)
    if any(outlet_id != user.locked_outlet_id for outlet_id in (body.branch_costs or {})):
        raise DomainError(BRANCH_LOCKED_OTHER, status=status.HTTP_403_FORBIDDEN)


def _guard(error: DomainError) -> HTTPException:
    return HTTPException(status_code=error.status, detail=error.message)


@router.get("/{menu_id}/fixed-cost", response_model=FixedCostOut)
def get_fixed_cost(
    menu_id: str,
    db: Session = Depends(get_db),
    _manage: User = Depends(require_permission(PERMISSION_MANAGE)),
    _cost: User = Depends(require_permission(PERMISSION_COST)),
):
    try:
        return _read(db, menu_id)
    except DomainError as error:
        raise _guard(error) from error


@router.patch("/{menu_id}/fixed-cost", response_model=FixedCostOut)
def set_fixed_cost(
    menu_id: str,
    body: FixedCostIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
    _cost: User = Depends(require_permission(PERMISSION_COST)),
):
    try:
        _branch_scope(user, body)
        item = catalog_menu.existing(db, menu_id)
        before = item.fixed_cost
        overrides = {outlet_id: value for outlet_id, value in (body.branch_costs or {}).items()}
        changed = fixed_cost.save(db, item, body.cost, overrides or None)
        db.commit()
    except DomainError as error:
        db.rollback()
        raise _guard(error) from error
    if changed:
        log.info("menu fixed cost set: user=%s menu=%s before=%s after=%s branch_overrides=%d", user.id, menu_id, before, item.fixed_cost, len(overrides))
    return _read(db, menu_id)


@router.delete("/{menu_id}/fixed-cost", status_code=status.HTTP_204_NO_CONTENT)
def clear_fixed_cost(
    menu_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
    _cost: User = Depends(require_permission(PERMISSION_COST)),
):
    try:
        if user.locked_outlet_id:
            raise DomainError(BRANCH_LOCKED_BASE, status=status.HTTP_403_FORBIDDEN)
        item = catalog_menu.existing(db, menu_id)
        before = item.fixed_cost
        changed = fixed_cost.clear(db, item)
        db.commit()
    except DomainError as error:
        db.rollback()
        raise _guard(error) from error
    if changed:
        log.info("menu fixed cost cleared: user=%s menu=%s before=%s", user.id, menu_id, before)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
