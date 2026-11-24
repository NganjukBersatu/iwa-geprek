"""The one door for variant groups and extras: their names, choices, branches, branch prices and the menus they go on."""
import re
import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.auth import AnyOf
from app.core.catalog import branch_scope
from app.core.errors import DomainError
from app.models.category import Category
from app.models.extra import Extra, ExtraOutletPrice, MenuExtra
from app.models.menu_item import MenuItem
from app.models.outlet import Outlet
from app.models.variant import MenuVariantGroup, VariantChoice, VariantGroup

PERMISSION_VARIANTS = "varian.kelola"
PERMISSION_EXTRAS = "ekstra.kelola"
# The menus and ingredients to pick from serve both variant groups and extras.
MANAGE_GATE = AnyOf((PERMISSION_VARIANTS, PERMISSION_EXTRAS))
EXTRA_CATEGORY_KIND = "ekstra"
COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")

NOT_FOUND = 404
CONFLICT = 409

GROUP_NOT_FOUND = "Kelompok varian tidak ditemukan."
GROUP_TAKEN = "Kelompok varian '{name}' sudah ada."
CHOICES_REQUIRED = "Isi minimal satu pilihan."
CHOICE_TWICE = "Ada dua pilihan dengan nama yang sama di kelompok ini."
CHOICE_NOT_FOUND = "Ada pilihan yang tidak ditemukan di kelompok ini."
COLOR_INVALID = "Warna harus berbentuk #RRGGBB."
EXTRA_NOT_FOUND = "Ekstra tidak ditemukan."
GROUP_ELSEWHERE = "Kelompok varian ini berlaku untuk semua cabang. Ubah dari web admin."
EXTRA_ELSEWHERE = "Ekstra ini berlaku untuk lebih dari satu cabang. Ubah dari web admin."
EXTRA_TAKEN = "Ekstra '{name}' sudah ada."
MENU_NOT_FOUND = "Ada menu yang tidak ditemukan."
BRANCH_UNKNOWN = "Ada cabang yang tidak ditemukan."
BRANCHES_REQUIRED = "Pilih minimal satu cabang, atau berlakukan di semua cabang."
CATEGORY_NOT_FOUND = "Kategori tidak ditemukan."


@dataclass(frozen=True)
class ChoiceInput:
    """An id keeps an existing choice; without one a new choice is made."""

    id: str | None
    name: str
    color: str | None
    is_active: bool


def _tidy(name: str) -> str:
    return " ".join(name.split())


def _next_position(db: Session, column) -> int:
    return (db.scalar(select(func.coalesce(func.max(column), -1))) or 0) + 1


def _checked_menus(db: Session, menu_ids: list[str]) -> list[str]:
    unique = list(dict.fromkeys(menu_ids))
    if unique and len(set(db.scalars(select(MenuItem.id).where(MenuItem.id.in_(unique))).all())) != len(unique):
        raise DomainError(MENU_NOT_FOUND, status=NOT_FOUND)
    return unique


def _checked_branches(db: Session, outlet_ids: list[str] | None) -> list[str] | None:
    if outlet_ids is None:
        return None
    unique = list(dict.fromkeys(outlet_ids))
    if not unique:
        raise DomainError(BRANCHES_REQUIRED)
    if len(set(db.scalars(select(Outlet.id).where(Outlet.id.in_(unique))).all())) != len(unique):
        raise DomainError(BRANCH_UNKNOWN, status=NOT_FOUND)
    return unique


def menus_of(db: Session, kind: str, owner_ids: list[str]) -> dict[str, list[str]]:
    """{group or extra id: menu ids} in one query."""
    if not owner_ids:
        return {}
    if kind == "varian":
        rows = db.execute(select(MenuVariantGroup.group_id, MenuVariantGroup.menu_item_id).where(MenuVariantGroup.group_id.in_(owner_ids))).all()
    else:
        rows = db.execute(select(MenuExtra.extra_id, MenuExtra.menu_item_id).where(MenuExtra.extra_id.in_(owner_ids))).all()
    result: dict[str, list[str]] = {}
    for owner, menu in rows:
        result.setdefault(owner, []).append(menu)
    return result


def _set_menus(db: Session, kind: str, owner_id: str, menu_ids: list[str]) -> None:
    unique = _checked_menus(db, menu_ids)
    if kind == "varian":
        db.execute(delete(MenuVariantGroup).where(MenuVariantGroup.group_id == owner_id))
        db.add_all([MenuVariantGroup(id=str(uuid.uuid4()), group_id=owner_id, menu_item_id=menu) for menu in unique])
    else:
        db.execute(delete(MenuExtra).where(MenuExtra.extra_id == owner_id))
        db.add_all([MenuExtra(id=str(uuid.uuid4()), extra_id=owner_id, menu_item_id=menu) for menu in unique])
    db.flush()


# --- Variant groups ---------------------------------------------------------------


def choices_of(db: Session, group_ids: list[str]) -> dict[str, list[VariantChoice]]:
    if not group_ids:
        return {}
    result: dict[str, list[VariantChoice]] = {}
    for choice in db.scalars(select(VariantChoice).where(VariantChoice.group_id.in_(group_ids)).order_by(VariantChoice.position)).all():
        result.setdefault(choice.group_id, []).append(choice)
    return result


def _group(db: Session, group_id: str, outlet_scope: str | None = None) -> VariantGroup:
    """With `outlet_scope` (a tablet) only a group of that branch alone is returned for changing; see branch_scope.guard."""
    group = db.get(VariantGroup, group_id)
    if group is None:
        raise DomainError(GROUP_NOT_FOUND, status=NOT_FOUND)
    branch_scope.guard(group.outlet_id, outlet_scope, GROUP_NOT_FOUND, GROUP_ELSEWHERE, NOT_FOUND)
    return group


def existing_group(db: Session, group_id: str, outlet_scope: str | None = None) -> VariantGroup:
    return _group(db, group_id, outlet_scope)


def get_group(db: Session, group_id: str) -> VariantGroup:
    """One group for its page; an unknown id answers as missing."""
    return _group(db, group_id)


def get_extra(db: Session, extra_id: str) -> Extra:
    """One extra for its page; an unknown id answers as missing."""
    return _extra(db, extra_id)


def _check_group_name(db: Session, name: str, outlet_id: str | None, except_id: str | None = None) -> None:
    """A name is taken only by a group that would show at the same branch: one for every branch, or one of the same branch."""
    for found in db.scalars(select(VariantGroup).where(func.lower(VariantGroup.name) == name.lower())).all():
        overlaps = found.outlet_id is None or outlet_id is None or found.outlet_id == outlet_id
        if found.id != except_id and overlaps:
            raise DomainError(GROUP_TAKEN.format(name=name), status=CONFLICT)


def _sync_choices(db: Session, group: VariantGroup, incoming: list[ChoiceInput]) -> None:
    """Choices with an id are updated, those without one are made, those left out go; past orders keep the copied names."""
    if not incoming:
        raise DomainError(CHOICES_REQUIRED)
    names = [_tidy(choice.name).lower() for choice in incoming]
    if len(names) != len(set(names)):
        raise DomainError(CHOICE_TWICE)
    current = {choice.id: choice for choice in choices_of(db, [group.id]).get(group.id, [])}
    kept: set[str] = set()
    for position, choice in enumerate(incoming):
        if choice.color and not COLOR_PATTERN.match(choice.color):
            raise DomainError(COLOR_INVALID)
        if choice.id:
            row = current.get(choice.id)
            if row is None:
                raise DomainError(CHOICE_NOT_FOUND, status=NOT_FOUND)
            row.name, row.color, row.is_active, row.position = _tidy(choice.name), choice.color or None, choice.is_active, position
            kept.add(choice.id)
        else:
            db.add(
                VariantChoice(
                    id=str(uuid.uuid4()), group_id=group.id, name=_tidy(choice.name), color=choice.color or None, position=position, is_active=choice.is_active
                )
            )
    for choice_id, row in current.items():
        if choice_id not in kept:
            db.delete(row)
    db.flush()


def create_group(
    db: Session, name: str, required: bool, active: bool, choices: list[ChoiceInput], menu_ids: list[str], outlet_id: str | None = None
) -> VariantGroup:
    name = _tidy(name)
    scope = branch_scope.checked(db, outlet_id)
    _check_group_name(db, name, scope)
    group = VariantGroup(
        id=str(uuid.uuid4()), name=name, required=required, is_active=active, position=_next_position(db, VariantGroup.position), outlet_id=scope
    )
    db.add(group)
    db.flush()
    _sync_choices(db, group, choices)
    _set_menus(db, "varian", group.id, menu_ids)
    db.commit()
    db.refresh(group)
    return group


def update_group(db: Session, group_id: str, changes: dict, outlet_scope: str | None = None) -> VariantGroup:
    """A tablet cannot move a group to another branch, so `outlet_id` in its changes is dropped."""
    group = _group(db, group_id, outlet_scope)
    if outlet_scope is not None:
        changes = {key: value for key, value in changes.items() if key != "outlet_id"}
    scope = branch_scope.checked(db, changes["outlet_id"]) if "outlet_id" in changes else group.outlet_id
    if changes.get("name") is not None or "outlet_id" in changes:
        name = _tidy(changes["name"]) if changes.get("name") is not None else group.name
        _check_group_name(db, name, scope, group.id)
        group.name = name
        group.outlet_id = scope
    if changes.get("required") is not None:
        group.required = changes["required"]
    if changes.get("is_active") is not None:
        group.is_active = changes["is_active"]
    if changes.get("choices") is not None:
        _sync_choices(db, group, changes["choices"])
    if changes.get("menu_ids") is not None:
        _set_menus(db, "varian", group.id, changes["menu_ids"])
    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, group_id: str, outlet_scope: str | None = None) -> None:
    """Its choices, their recipes and its menu links go in the database; past orders keep the copied names."""
    db.delete(_group(db, group_id, outlet_scope))
    db.commit()


# --- Extras ----------------------------------------------------------------------------


def branch_prices_of(db: Session, extra_ids: list[str]) -> dict[str, dict[str, Decimal]]:
    if not extra_ids:
        return {}
    result: dict[str, dict[str, Decimal]] = {}
    for row in db.scalars(select(ExtraOutletPrice).where(ExtraOutletPrice.extra_id.in_(extra_ids))).all():
        result.setdefault(row.extra_id, {})[row.outlet_id] = row.price
    return result


def _extra(db: Session, extra_id: str, outlet_scope: str | None = None) -> Extra:
    """With `outlet_scope` (a tablet) only an extra listed for that branch alone is returned for changing."""
    extra = db.get(Extra, extra_id)
    if extra is None or (outlet_scope is not None and not branch_scope.listed_at(extra.outlet_ids, outlet_scope)):
        raise DomainError(EXTRA_NOT_FOUND, status=NOT_FOUND)
    if outlet_scope is not None and not branch_scope.listed_only_at(extra.outlet_ids, outlet_scope):
        raise DomainError(EXTRA_ELSEWHERE, status=branch_scope.FORBIDDEN)
    return extra


def existing_extra(db: Session, extra_id: str, outlet_scope: str | None = None) -> Extra:
    return _extra(db, extra_id, outlet_scope)


def _check_extra_name(db: Session, name: str, except_id: str | None = None) -> None:
    found = db.scalar(select(Extra).where(func.lower(Extra.name) == name.lower()))
    if found is not None and found.id != except_id:
        raise DomainError(EXTRA_TAKEN.format(name=name), status=CONFLICT)


def _checked_category(db: Session, category_id: str | None) -> str | None:
    if not category_id:
        return None
    if db.scalar(select(Category.id).where(Category.id == category_id, Category.kind == EXTRA_CATEGORY_KIND)) is None:
        raise DomainError(CATEGORY_NOT_FOUND)
    return category_id


def _set_branch_prices(db: Session, extra_id: str, prices: dict[str, Decimal | None] | None) -> None:
    """A figure keeps a branch price, None removes it so the branch follows the base price; branches left out stay."""
    if not prices:
        return
    _checked_branches(db, list(prices))
    current = {row.outlet_id: row for row in db.scalars(select(ExtraOutletPrice).where(ExtraOutletPrice.extra_id == extra_id)).all()}
    for outlet_id, price in prices.items():
        row = current.get(outlet_id)
        if price is None:
            if row is not None:
                db.delete(row)
        elif row is not None:
            row.price = price
        else:
            db.add(ExtraOutletPrice(id=str(uuid.uuid4()), extra_id=extra_id, outlet_id=outlet_id, price=price))
    db.flush()


def create_extra(
    db: Session,
    name: str,
    price: Decimal,
    active: bool,
    outlet_ids: list[str] | None,
    branch_prices: dict[str, Decimal | None] | None,
    category_id: str | None,
    menu_ids: list[str],
) -> Extra:
    name = _tidy(name)
    _check_extra_name(db, name)
    extra = Extra(
        id=str(uuid.uuid4()),
        name=name,
        price=price,
        is_active=active,
        outlet_ids=_checked_branches(db, outlet_ids),
        category_id=_checked_category(db, category_id),
        position=_next_position(db, Extra.position),
    )
    db.add(extra)
    db.flush()
    _set_branch_prices(db, extra.id, branch_prices)
    _set_menus(db, "ekstra", extra.id, menu_ids)
    db.commit()
    db.refresh(extra)
    return extra


def update_extra(db: Session, extra_id: str, changes: dict, outlet_scope: str | None = None) -> Extra:
    """`outlet_ids` sent empty sells the extra everywhere again; a field left out stays. A tablet changes neither the branches nor the branch prices."""
    extra = _extra(db, extra_id, outlet_scope)
    if outlet_scope is not None:
        changes = {key: value for key, value in changes.items() if key not in ("outlet_ids", "branch_prices")}
    if changes.get("name") is not None:
        name = _tidy(changes["name"])
        _check_extra_name(db, name, extra.id)
        extra.name = name
    if changes.get("price") is not None:
        extra.price = changes["price"]
    if changes.get("is_active") is not None:
        extra.is_active = changes["is_active"]
    if "category_id" in changes:
        extra.category_id = _checked_category(db, changes["category_id"])
    if "outlet_ids" in changes:
        extra.outlet_ids = _checked_branches(db, changes["outlet_ids"])
    _set_branch_prices(db, extra.id, changes.get("branch_prices"))
    if changes.get("menu_ids") is not None:
        _set_menus(db, "ekstra", extra.id, changes["menu_ids"])
    db.commit()
    db.refresh(extra)
    return extra


def delete_extra(db: Session, extra_id: str, outlet_scope: str | None = None) -> None:
    """Its branch prices, recipes and menu links go in the database; past orders keep the copied name and price."""
    db.delete(_extra(db, extra_id, outlet_scope))
    db.commit()
