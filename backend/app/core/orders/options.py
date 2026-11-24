"""Variants and extras chosen on one order line: checked against the menu, priced on the server."""
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.catalog import branch_scope
from app.core.errors import DomainError
from app.core.money import ZERO
from app.core.orders import recipes as recipe_rules
from app.models.extra import Extra, ExtraOutletPrice, MenuExtra
from app.models.menu_item import MenuItem
from app.models.order_item_option import EXTRA, VARIANT, OrderItemOption
from app.models.variant import MenuVariantGroup, VariantChoice, VariantGroup

DUPLICATE_VARIANT = "Pilihan varian untuk {menu} terkirim ganda."
DUPLICATE_EXTRA = "Ekstra untuk {menu} terkirim ganda; gabungkan jumlahnya."
VARIANT_NOT_FOR_MENU = "Pilihan varian tidak berlaku untuk {menu}."
ONE_PER_GROUP = "{menu}: hanya boleh satu pilihan di '{group}'."
GROUP_REQUIRED = "{menu}: pilih dulu '{group}'."
EXTRA_NOT_FOR_MENU = "Ekstra tidak berlaku untuk {menu} di cabang ini."


@dataclass(frozen=True)
class ExtraPick:
    extra_id: str
    qty: int


@dataclass
class ResolvedOptions:
    options: list[OrderItemOption] = field(default_factory=list)
    extra_per_portion: Decimal = ZERO
    # Cost added to one portion by the recipes of the chosen options; None when none of them has a recipe.
    extra_cost: Decimal | None = None
    # Key "kind:id" to the recipe it uses, and how many of it one portion of the menu item takes.
    recipes: dict[str, list[recipe_rules.RecipeLine]] = field(default_factory=dict)
    multiplier: dict[str, int] = field(default_factory=dict)

    def usages(self, portions: int) -> list[tuple[list[recipe_rules.RecipeLine], int]]:
        return [(self.recipes[key], self.multiplier[key] * portions) for key in self.recipes]


def _sold_at(extra: Extra, outlet_id: str) -> bool:
    return branch_scope.listed_at(extra.outlet_ids, outlet_id)


def resolve(
    db: Session,
    outlet_id: str,
    menu: MenuItem,
    variant_ids: list[str],
    extras: list[ExtraPick],
    kept_extra_prices: dict[str, Decimal],
) -> ResolvedOptions:
    """`kept_extra_prices` only matters when editing: an extra already on the order keeps the price it was sold at."""
    result = ResolvedOptions()
    if len(set(variant_ids)) != len(variant_ids):
        raise DomainError(DUPLICATE_VARIANT.format(menu=menu.name))
    extra_ids = [pick.extra_id for pick in extras]
    if len(set(extra_ids)) != len(extra_ids):
        raise DomainError(DUPLICATE_EXTRA.format(menu=menu.name))

    groups = db.scalars(
        select(VariantGroup)
        .join(MenuVariantGroup, MenuVariantGroup.group_id == VariantGroup.id)
        .where(
            MenuVariantGroup.menu_item_id == menu.id,
            VariantGroup.is_active.is_(True),
            or_(VariantGroup.outlet_id.is_(None), VariantGroup.outlet_id == outlet_id),
        )
        .order_by(VariantGroup.position, VariantGroup.id)
    ).all()
    choices = db.scalars(
        select(VariantChoice).where(VariantChoice.group_id.in_([group.id for group in groups]), VariantChoice.is_active.is_(True))
    ).all() if groups else []
    group_of = {group.id: group for group in groups}
    valid = {choice.id: choice for choice in choices}
    picked: dict[str, VariantChoice] = {}
    for choice_id in variant_ids:
        choice = valid.get(choice_id)
        if choice is None:
            raise DomainError(VARIANT_NOT_FOR_MENU.format(menu=menu.name))
        if choice.group_id in picked:
            raise DomainError(ONE_PER_GROUP.format(menu=menu.name, group=group_of[choice.group_id].name))
        picked[choice.group_id] = choice
    for group in groups:
        has_choices = any(choice.group_id == group.id for choice in choices)
        if group.required and group.id not in picked and has_choices:
            raise DomainError(GROUP_REQUIRED.format(menu=menu.name, group=group.name))
    for group in groups:
        choice = picked.get(group.id)
        if choice is not None:
            result.options.append(
                OrderItemOption(id=str(uuid.uuid4()), kind=VARIANT, ref_id=choice.id, group_name=group.name, name=choice.name, color=choice.color, price=ZERO, qty=1)
            )

    if extras:
        found = {
            extra.id: extra
            for extra in db.scalars(
                select(Extra)
                .join(MenuExtra, MenuExtra.extra_id == Extra.id)
                .where(MenuExtra.menu_item_id == menu.id, Extra.id.in_(extra_ids), Extra.is_active.is_(True))
            ).all()
        }
        branch_price = {
            row.extra_id: row.price
            for row in db.scalars(select(ExtraOutletPrice).where(ExtraOutletPrice.extra_id.in_(list(found)), ExtraOutletPrice.outlet_id == outlet_id)).all()
        }
        for pick in extras:
            extra = found.get(pick.extra_id)
            if extra is None or not _sold_at(extra, outlet_id):
                raise DomainError(EXTRA_NOT_FOR_MENU.format(menu=menu.name))
            price = kept_extra_prices.get(extra.id, Decimal(str(branch_price.get(extra.id, extra.price))))
            result.options.append(OrderItemOption(id=str(uuid.uuid4()), kind=EXTRA, ref_id=extra.id, name=extra.name, price=price, qty=pick.qty))
            result.extra_per_portion += price * pick.qty

    variant_recipes = recipe_rules.of_options(db, recipe_rules.KIND_VARIANT, [o.ref_id for o in result.options if o.kind == VARIANT], outlet_id)
    extra_recipes = recipe_rules.of_options(db, recipe_rules.KIND_EXTRA, [o.ref_id for o in result.options if o.kind == EXTRA], outlet_id)
    total: Decimal | None = None
    for option in result.options:
        lines = (variant_recipes if option.kind == VARIANT else extra_recipes).get(option.ref_id, [])
        cost = recipe_rules.cost_of(lines)
        option.unit_cost = cost
        if lines:
            key = f"{option.kind}:{option.ref_id}"
            result.recipes[key] = lines
            result.multiplier[key] = option.qty
        if cost is not None:
            total = (total or ZERO) + cost * option.qty
    result.extra_cost = total
    return result
