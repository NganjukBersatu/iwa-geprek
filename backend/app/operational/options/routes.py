"""Variant groups and extras on the tablet; every rule lives in app.core.catalog.options, recipes stay on the web."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.auth import require_gate, require_permission
from app.core.catalog import branch_scope, options
from app.core.database import get_db
from app.core.errors import DomainError
from app.models.extra import Extra
from app.models.menu_item import MenuItem
from app.models.user import User
from app.models.variant import VariantGroup
from app.operational.device import tablet_outlet_id
from app.operational.options.schemas import ChoiceIn, OptionChoiceOut, OptionExtraIn, OptionExtraOut, GroupIn, OptionGroupOut, MenuChoiceOut

router = APIRouter(prefix="/options", tags=["v2-operational-options"])



@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _choices(choices: list[ChoiceIn]) -> list[options.ChoiceInput]:
    return [options.ChoiceInput(choice.id, choice.name, choice.color, choice.is_active) for choice in choices]


def _groups_out(db: Session, groups: list[VariantGroup], outlet_id: str) -> list[OptionGroupOut]:
    ids = [group.id for group in groups]
    choices = options.choices_of(db, ids)
    menus = options.menus_of(db, "varian", ids)
    return [
        OptionGroupOut(
            id=group.id,
            name=group.name,
            required=group.required,
            is_active=group.is_active,
            choices=[OptionChoiceOut(id=choice.id, name=choice.name, color=choice.color, is_active=choice.is_active) for choice in choices.get(group.id, [])],
            menu_ids=menus.get(group.id, []),
            editable=branch_scope.owned_by(group.outlet_id, outlet_id),
        )
        for group in groups
    ]


def _extras_out(db: Session, extras: list[Extra], outlet_id: str) -> list[OptionExtraOut]:
    menus = options.menus_of(db, "ekstra", [extra.id for extra in extras])
    return [
        OptionExtraOut(
            id=extra.id,
            name=extra.name,
            price=extra.price,
            is_active=extra.is_active,
            menu_ids=menus.get(extra.id, []),
            editable=branch_scope.listed_only_at(extra.outlet_ids, outlet_id),
        )
        for extra in extras
    ]


may_manage_options = require_gate(options.MANAGE_GATE)


@router.get("/variant-groups", response_model=list[OptionGroupOut])
def list_groups(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_VARIANTS)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    """Groups for every branch and those of this branch only; another branch's groups are not shown."""
    rows = db.scalars(
        select(VariantGroup).where(or_(VariantGroup.outlet_id.is_(None), VariantGroup.outlet_id == outlet_id)).order_by(VariantGroup.position, VariantGroup.name)
    ).all()
    return _groups_out(db, list(rows), outlet_id)


@router.post("/variant-groups", response_model=OptionGroupOut, status_code=status.HTTP_201_CREATED)
def create_group(
    body: GroupIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_VARIANTS)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    """A group made on a tablet belongs to that tablet's branch."""
    with _domain_errors():
        group = options.create_group(db, body.name, body.required, body.is_active, _choices(body.choices), body.menu_ids, outlet_id)
    return _groups_out(db, [group], outlet_id)[0]


@router.put("/variant-groups/{group_id}", response_model=OptionGroupOut)
def update_group(
    group_id: str,
    body: GroupIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_VARIANTS)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    """The whole form is sent, so choices left out are removed, as on the web."""
    changes = {"name": body.name, "required": body.required, "is_active": body.is_active, "choices": _choices(body.choices), "menu_ids": body.menu_ids}
    with _domain_errors():
        group = options.update_group(db, group_id, changes, outlet_id)
    return _groups_out(db, [group], outlet_id)[0]


@router.delete("/variant-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_VARIANTS)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    with _domain_errors():
        options.delete_group(db, group_id, outlet_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/extras", response_model=list[OptionExtraOut])
def list_extras(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_EXTRAS)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    rows = [extra for extra in db.scalars(select(Extra).order_by(Extra.position, Extra.name)).all() if branch_scope.listed_at(extra.outlet_ids, outlet_id)]
    return _extras_out(db, rows, outlet_id)


@router.post("/extras", response_model=OptionExtraOut, status_code=status.HTTP_201_CREATED)
def create_extra(
    body: OptionExtraIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_EXTRAS)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    """An extra made on a tablet is sold at that tablet's branch only."""
    with _domain_errors():
        extra = options.create_extra(db, body.name, body.price, body.is_active, [outlet_id], None, None, body.menu_ids)
    return _extras_out(db, [extra], outlet_id)[0]


@router.put("/extras/{extra_id}", response_model=OptionExtraOut)
def update_extra(
    extra_id: str,
    body: OptionExtraIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_EXTRAS)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    changes = {"name": body.name, "price": body.price, "is_active": body.is_active, "menu_ids": body.menu_ids}
    with _domain_errors():
        extra = options.update_extra(db, extra_id, changes, outlet_id)
    return _extras_out(db, [extra], outlet_id)[0]


@router.delete("/extras/{extra_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_extra(
    extra_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(options.PERMISSION_EXTRAS)),
    outlet_id: str = Depends(tablet_outlet_id),
):
    with _domain_errors():
        options.delete_extra(db, extra_id, outlet_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/menus", response_model=list[MenuChoiceOut])
def menus(db: Session = Depends(get_db), _: User = Depends(may_manage_options), outlet_id: str = Depends(tablet_outlet_id)):
    """The menus this branch sells by name, to choose which ones a group or an extra goes on."""
    rows = db.execute(select(MenuItem.id, MenuItem.name).where(branch_scope.listed_at_clause(MenuItem.outlet_ids, outlet_id)).order_by(MenuItem.name)).all()
    return [MenuChoiceOut(id=menu_id, name=name) for menu_id, name in rows]
