"""What one branch sells right now: its menus at the branch price, with the variants and extras each may take."""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.catalog import branch_scope
from app.core.pricing import price_map
from app.models.extra import Extra, ExtraOutletPrice, MenuExtra
from app.models.menu_item import MenuItem
from app.models.variant import MenuVariantGroup, VariantChoice, VariantGroup


@dataclass(frozen=True)
class Choice:
    id: str
    name: str


@dataclass(frozen=True)
class VariantOptions:
    id: str
    name: str
    required: bool
    choices: list[Choice]


@dataclass(frozen=True)
class ExtraOption:
    id: str
    name: str
    price: Decimal


@dataclass(frozen=True)
class SellableMenu:
    menu: MenuItem
    price: Decimal
    variant_groups: list[VariantOptions]
    extras: list[ExtraOption]


def menus_of(db: Session, outlet_id: str, only: set[str] | None = None) -> list[SellableMenu]:
    """Every menu the branch sells, available or not, so the till can show what is sold out; a fixed number of queries. `only` narrows it to those menus."""
    statement = select(MenuItem).order_by(MenuItem.name)
    if only is not None:
        statement = statement.where(MenuItem.id.in_(only))
    menus = [menu for menu in db.scalars(statement).all() if branch_scope.listed_at(menu.outlet_ids, outlet_id)]
    menu_ids = [menu.id for menu in menus]
    prices = price_map(db, outlet_id, menus)

    groups_of: dict[str, list[str]] = {}
    for link in db.scalars(select(MenuVariantGroup).where(MenuVariantGroup.menu_item_id.in_(menu_ids))).all():
        groups_of.setdefault(link.menu_item_id, []).append(link.group_id)
    groups = {
        group.id: group
        for group in db.scalars(select(VariantGroup).where(VariantGroup.is_active.is_(True), or_(VariantGroup.outlet_id.is_(None), VariantGroup.outlet_id == outlet_id))).all()
    }
    choices_of: dict[str, list[VariantChoice]] = {}
    for choice in db.scalars(select(VariantChoice).where(VariantChoice.is_active.is_(True)).order_by(VariantChoice.position, VariantChoice.id)).all():
        choices_of.setdefault(choice.group_id, []).append(choice)

    extras = {extra.id: extra for extra in db.scalars(select(Extra).where(Extra.is_active.is_(True))).all() if branch_scope.listed_at(extra.outlet_ids, outlet_id)}
    branch_price = {row.extra_id: row.price for row in db.scalars(select(ExtraOutletPrice).where(ExtraOutletPrice.outlet_id == outlet_id)).all()}
    extras_of: dict[str, list[str]] = {}
    for link in db.scalars(select(MenuExtra).where(MenuExtra.menu_item_id.in_(menu_ids))).all():
        if link.extra_id in extras:
            extras_of.setdefault(link.menu_item_id, []).append(link.extra_id)

    def variant_groups(menu_id: str) -> list[VariantOptions]:
        # A group without an active choice offers nothing to pick, so it is left out.
        ids = sorted((gid for gid in groups_of.get(menu_id, []) if gid in groups and choices_of.get(gid)), key=lambda gid: (groups[gid].position, groups[gid].name.lower()))
        return [
            VariantOptions(id=gid, name=groups[gid].name, required=groups[gid].required, choices=[Choice(id=choice.id, name=choice.name) for choice in choices_of[gid]])
            for gid in ids
        ]

    def extra_options(menu_id: str) -> list[ExtraOption]:
        ids = sorted(extras_of.get(menu_id, []), key=lambda eid: (extras[eid].position, extras[eid].name.lower()))
        return [ExtraOption(id=eid, name=extras[eid].name, price=Decimal(str(branch_price.get(eid, extras[eid].price)))) for eid in ids]

    return [SellableMenu(menu=menu, price=prices[menu.id], variant_groups=variant_groups(menu.id), extras=extra_options(menu.id)) for menu in menus]
