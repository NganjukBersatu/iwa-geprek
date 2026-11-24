"""Menus and promotions: margins, recipes, menus that belong in one with a variant, menus nobody buys, and promotions."""
import re
from datetime import timedelta

from sqlalchemy import exists, select

from app.core.catalog import fixed_cost, recipe_costing
from app.core.clock import as_aware
from app.core.orders.recipes import cost_of, of_menus_many
from app.core.pricing import price_map_many
from app.models.cafe_promotion import CafePromotion
from app.models.cafe_settings import CafeSettings
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.promo import Promo
from app.models.stock import StockItem
from web.management.issues import constants as c
from web.management.issues.domain import Issue, IssueKind, IssueLevel, Scope

_WORD = re.compile(r"[a-z0-9]+")


def _offered_at(menu: MenuItem, outlet_id: str) -> bool:
    """The rule of the till: no branch list means every branch."""
    return not menu.outlet_ids or outlet_id in menu.outlet_ids


def _available_menus(scope: Scope) -> list[MenuItem]:
    return list(scope.db.scalars(select(MenuItem).where(MenuItem.is_available.is_(True)).order_by(MenuItem.name)).all())


def recipes_and_margins(scope: Scope) -> list[Issue]:
    """Per branch selling the menu, by the Master Resep costing. Margin: percent below compared (the target). A resold item has stock, not a recipe."""
    menus = _available_menus(scope)
    if not menus or not scope.outlet_ids:
        return []
    menu_ids = [menu.id for menu in menus]
    lines = of_menus_many(scope.db, scope.outlet_ids, menu_ids)
    settings = {item.outlet_id: item for item in scope.db.scalars(select(CafeSettings).where(CafeSettings.outlet_id.in_(scope.outlet_ids))).all()}
    prices = price_map_many(scope.db, scope.outlet_ids, menus, settings)
    manual = recipe_costing.manual_of_many(scope.db, scope.outlet_ids, menu_ids)
    resold = set(scope.db.execute(select(StockItem.outlet_id, StockItem.menu_item_id).where(StockItem.outlet_id.in_(scope.outlet_ids))).tuples().all())
    fixed = fixed_cost.of_menus_many(scope.db, scope.outlet_ids, menu_ids)
    issues: list[Issue] = []
    for outlet_id in scope.outlet_ids:
        for menu in menus:
            key = (outlet_id, menu.id)
            if not _offered_at(menu, outlet_id) or key in resold:
                continue
            if key in fixed:
                # A fixed cost is the cost itself: no add cost or overhead is laid on it, so the margin is the price less that cost.
                figures = recipe_costing.costing_of_fixed(fixed[key], prices[key], settings.get(outlet_id))
                if figures.margin_percent is not None and figures.target_margin_percent is not None and figures.margin_percent < figures.target_margin_percent:
                    issues.append(
                        Issue(IssueKind.MARGIN_BELOW_TARGET, IssueLevel.WARNING, outlet_id, menu.id, menu.name, percent=figures.margin_percent, compared=figures.target_margin_percent)
                    )
                continue
            menu_lines = lines.get(key, [])
            if not menu_lines:
                issues.append(Issue(IssueKind.MENU_WITHOUT_RECIPE, IssueLevel.WARNING, outlet_id, menu.id, menu.name))
                continue
            figures = recipe_costing.costing(cost_of(menu_lines), prices[key], manual.get(key), settings.get(outlet_id))
            if figures.margin_percent is not None and figures.target_margin_percent is not None and figures.margin_percent < figures.target_margin_percent:
                issues.append(
                    Issue(IssueKind.MARGIN_BELOW_TARGET, IssueLevel.WARNING, outlet_id, menu.id, menu.name, percent=figures.margin_percent, compared=figures.target_margin_percent)
                )
    return issues


def menus_for_one_variant(scope: Scope) -> list[Issue]:
    """Menus of one category whose names differ only by a temperature or size word. subject: the shared name, count: how many menus."""
    groups: dict[tuple[str | None, tuple[str, ...]], list[MenuItem]] = {}
    marked: set[tuple[str | None, tuple[str, ...]]] = set()
    for menu in _available_menus(scope):
        if not any(_offered_at(menu, outlet_id) for outlet_id in scope.outlet_ids):
            continue
        words = _WORD.findall(menu.name.lower())
        key = (menu.category_id, tuple(word for word in words if word not in c.VARIANT_WORDS))
        if not key[1]:
            continue
        # The plain name joins the group too; a group of the same name with no variant word in it is a duplicate, not a variant.
        groups.setdefault(key, []).append(menu)
        if len(key[1]) < len(words):
            marked.add(key)
    return [
        Issue(IssueKind.MENU_SHOULD_BE_VARIANT, IssueLevel.SUGGESTION, None, members[0].id, _without_variant_words(members[0].name), count=len(members))
        for key, members in groups.items()
        if key in marked and len(members) > 1
    ]


def _without_variant_words(name: str) -> str:
    """The name as the owner typed it, less the temperature and size words."""
    return " ".join(part for part in name.split() if "".join(_WORD.findall(part.lower())) not in c.VARIANT_WORDS)


def unsold_menus(scope: Scope) -> list[Issue]:
    """Offered at the branch for longer than the window and not in one valid order there since."""
    since = scope.now - timedelta(days=c.UNSOLD_MENU_DAYS)
    sold = set(
        scope.db.execute(
            select(Order.outlet_id, OrderItem.menu_item_id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.outlet_id.in_(scope.outlet_ids), Order.business_day >= scope.first_day(c.UNSOLD_MENU_DAYS), Order.voided_at.is_(None), OrderItem.menu_item_id.is_not(None))
            .distinct()
        )
        .tuples()
        .all()
    )
    return [
        Issue(IssueKind.MENU_UNSOLD, IssueLevel.SUGGESTION, outlet_id, menu.id, menu.name)
        for menu in _available_menus(scope)
        if menu.created_at is not None and as_aware(menu.created_at) < since
        for outlet_id in scope.outlet_ids
        if _offered_at(menu, outlet_id) and (outlet_id, menu.id) not in sold
    ]


def promotions_ending(scope: Scope) -> list[Issue]:
    """Discounts and announcements running now that end within the window. day: the last day."""
    last = scope.today + timedelta(days=c.PROMO_ENDING_DAYS)
    issues: list[Issue] = []
    for model, name in ((Promo, Promo.name), (CafePromotion, CafePromotion.title)):
        rows = scope.db.execute(
            select(model.id, name, model.ends_on).where(model.is_active.is_(True), model.starts_on <= scope.today, model.ends_on >= scope.today, model.ends_on <= last)
        ).all()
        issues.extend(Issue(IssueKind.PROMO_ENDING, IssueLevel.NOTICE, None, promo_id, title, day=ends_on) for promo_id, title, ends_on in rows)
    return issues


def unused_promos(scope: Scope) -> list[Issue]:
    """Discounts running for at least the window and not used once at the branches asked for. day: the first day it ran."""
    used = exists().where(Order.promo_id == Promo.id, Order.outlet_id.in_(scope.outlet_ids), Order.voided_at.is_(None))
    rows = scope.db.execute(
        select(Promo.id, Promo.name, Promo.starts_on).where(
            Promo.is_active.is_(True), Promo.starts_on <= scope.today - timedelta(days=c.PROMO_UNUSED_DAYS), Promo.ends_on >= scope.today, ~used
        )
    ).all()
    return [Issue(IssueKind.PROMO_UNUSED, IssueLevel.SUGGESTION, None, promo_id, name, day=starts_on) for promo_id, name, starts_on in rows]
