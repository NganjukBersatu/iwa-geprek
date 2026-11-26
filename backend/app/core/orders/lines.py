"""Writing the lines of an order with their stock and ingredient cards; creating and correcting an order both come through here."""
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.catalog import availability, branch_scope, fixed_cost
from app.core.errors import DomainError
from app.core.money import ZERO
from app.core.orders import options as option_rules
from app.core.orders import recipes, stock
from app.core.pricing import price_map
from app.models.ingredient import Ingredient, RecipeIngredient
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.stock import StockItem
from app.models.user import User

NOT_FOUND = 404
MENU_NOT_FOUND = "Menu tidak ditemukan."
MENU_NOT_SOLD = "Menu {menu} tidak dijual di cabang ini."
MENU_UNAVAILABLE = "Menu {menu} sedang tidak tersedia."
MENU_INGREDIENT_OUT = "Menu {menu} tidak bisa dipesan: bahan {ingredients} habis."
MENU_WITHOUT_RECIPE = "Menu {menu} belum punya resep atau harga pokok. Isi dulu di Master Resep, atau isi harga pokok tetap di menu."


@dataclass(frozen=True)
class LineInput:
    menu_item_id: str
    qty: int
    note: str | None
    variant_ids: list[str]
    extras: list[option_rules.ExtraPick]


@dataclass(frozen=True)
class SoldAt:
    """What an existing line was sold at; the menu part of the cost, without the options' share."""

    price: Decimal
    cost: Decimal | None


@dataclass(frozen=True)
class Kept:
    """Prices a correction keeps from the lines it replaces; a new sale keeps nothing."""

    menus: dict[str, SoldAt] = field(default_factory=dict)
    extra_prices: dict[str, Decimal] = field(default_factory=dict)


@dataclass(frozen=True)
class WrittenLines:
    promo_basis: list[tuple[str, Decimal]]
    subtotal: Decimal


def is_sold_at(menu: MenuItem, outlet_id: str) -> bool:
    return branch_scope.listed_at(menu.outlet_ids, outlet_id)


def ready_ids(db: Session, outlet_id: str | None, menu_ids: list[str]) -> set[str]:
    """A menu is ready to sell where its cost is known: it has a recipe, its stock is tracked, or it has a fixed cost."""
    if not menu_ids:
        return set()
    recipes = select(RecipeIngredient.menu_item_id).where(RecipeIngredient.menu_item_id.in_(menu_ids))
    stocks = select(StockItem.menu_item_id).where(StockItem.menu_item_id.in_(menu_ids), StockItem.is_tracked.is_(True))
    fixed = select(MenuItem.id).where(MenuItem.id.in_(menu_ids), MenuItem.fixed_cost.is_not(None))
    if outlet_id:
        recipes = recipes.where(RecipeIngredient.outlet_id == outlet_id)
        stocks = stocks.where(StockItem.outlet_id == outlet_id)
    return set(db.scalars(recipes).all()) | set(db.scalars(stocks).all()) | set(db.scalars(fixed).all())


def missing_ingredients(db: Session, outlet_id: str | None, menu_ids: list[str]) -> dict[str, list[str]]:
    """Names of the ingredients marked out of stock in each menu's recipe, in one query."""
    if not menu_ids:
        return {}
    statement = (
        select(RecipeIngredient.menu_item_id, Ingredient.name)
        .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
        .where(RecipeIngredient.menu_item_id.in_(menu_ids), Ingredient.is_available.is_(False))
    )
    if outlet_id:
        statement = statement.where(RecipeIngredient.outlet_id == outlet_id)
    result: dict[str, list[str]] = {}
    for menu_id, name in db.execute(statement).all():
        names = result.setdefault(menu_id, [])
        if name not in names:
            names.append(name)
    return result


def write(db: Session, user: User, order: Order, lines: list[LineInput], kept: Kept, stock_note: str | None, check_sellable: bool) -> WrittenLines:
    """`check_sellable` refuses what the cashier may not sell right now; a correction of a past sale skips it."""
    menu_ids = [line.menu_item_id for line in lines]
    menu_recipes = recipes.of_menus(db, order.outlet_id, menu_ids)
    fixed_costs = fixed_cost.of_menus(db, order.outlet_id, menu_ids)
    out_of_stock = missing_ingredients(db, order.outlet_id, menu_ids) if check_sellable else {}
    marked_out = availability.off_ids(db, order.outlet_id, menu_ids) if check_sellable else set()
    menus = {menu.id: menu for menu in db.scalars(select(MenuItem).where(MenuItem.id.in_(menu_ids))).all()} if menu_ids else {}
    usages: list[tuple[list[recipes.RecipeLine], int]] = []
    promo_basis: list[tuple[str, Decimal]] = []
    subtotal = ZERO
    for line in lines:
        menu = menus.get(line.menu_item_id)
        if menu is None:
            raise DomainError(MENU_NOT_FOUND, status=NOT_FOUND)
        if check_sellable:
            if not menu.is_available or menu.id in marked_out:
                raise DomainError(MENU_UNAVAILABLE.format(menu=menu.name))
            if menu.id in out_of_stock:
                raise DomainError(MENU_INGREDIENT_OUT.format(menu=menu.name, ingredients=", ".join(out_of_stock[menu.id])))
        sold = kept.menus.get(menu.id)
        if sold is not None:
            price, cost = sold.price, sold.cost
        else:
            if not is_sold_at(menu, order.outlet_id):
                raise DomainError(MENU_NOT_SOLD.format(menu=menu.name))
            price = price_map(db, order.outlet_id, [menu])[menu.id]
            if stock.is_tracked(db, order.outlet_id, menu.id):
                cost = stock.current_cost(db, order.outlet_id, menu.id)
            elif menu.id in fixed_costs:
                cost = fixed_costs[menu.id]
            else:
                # No menu is sold before its recipe exists, or the profit would read higher than it is.
                recipe = menu_recipes.get(menu.id, [])
                if not recipe:
                    raise DomainError(MENU_WITHOUT_RECIPE.format(menu=menu.name))
                cost = recipes.cost_of(recipe)
        chosen = option_rules.resolve(db, order.outlet_id, menu, line.variant_ids, line.extras, kept.extra_prices)
        line_subtotal = (price + chosen.extra_per_portion) * line.qty
        subtotal += line_subtotal
        if cost is not None and chosen.extra_cost is not None:
            cost += chosen.extra_cost
        promo_basis.append((menu.id, price * line.qty))
        usages.append((menu_recipes.get(menu.id, []), line.qty))
        usages.extend(chosen.usages(line.qty))

        item = OrderItem(
            id=str(uuid.uuid4()),
            order_id=order.id,
            menu_item_id=menu.id,
            menu_item_name=menu.name,
            unit_price=price,
            unit_cost=cost,
            qty=line.qty,
            subtotal=line_subtotal,
            note=(line.note or "").strip() or None,
        )
        db.add(item)
        for option in chosen.options:
            option.order_item_id = item.id
            db.add(option)
        if stock.is_tracked(db, order.outlet_id, menu.id):
            stock.record_sale(db, order.outlet_id, menu, line.qty, order.id, user.id, stock_note)
    recipes.use_up(db, order.outlet_id, order.id, user.id, usages)
    return WrittenLines(promo_basis=promo_basis, subtotal=subtotal)
