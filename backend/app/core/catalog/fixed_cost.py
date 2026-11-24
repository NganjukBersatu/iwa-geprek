"""The one door for a menu's fixed cost: a menu without a recipe whose cost is typed in, once for every branch or per branch."""
from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import delete, exists, select
from sqlalchemy.orm import Session

from app.core import money
from app.core.errors import DomainError
from app.models.ingredient import RecipeIngredient
from app.models.menu_item import MenuItem, MenuOutletCost
from app.models.outlet import Outlet
from app.models.stock import StockItem

CENTS = Decimal("0.01")
# Sama dengan batas CHECK di database: biaya satu porsi tidak pernah sebesar ini.
LIMIT = Decimal("100000000")

COST_INVALID = "Harga pokok harus angka 0 atau lebih dan kurang dari 100.000.000."
HAS_RECIPE = "Menu ini sudah punya resep. Kosongkan resepnya di Master Resep sebelum memakai harga pokok tetap."
HAS_FIXED_COST = "Menu ini memakai harga pokok tetap. Hapus harga pokok tetapnya di menu sebelum mengisi resep."
HAS_STOCK = "Menu ini dikelola sebagai barang berstok. Lepas dulu dari Barang jual-ulang sebelum memakai harga pokok tetap."
STOCK_HAS_FIXED_COST = "Menu ini memakai harga pokok tetap. Hapus harga pokok tetapnya di menu sebelum menandainya sebagai barang berstok."
BRANCH_UNKNOWN = "Cabang tidak dikenal."
BRANCH_COST_WITHOUT_BASE = "Isi harga pokok tetap menu ini dulu sebelum menetapkan harga pokok per cabang."


def checked(cost: Decimal) -> Decimal:
    """The figure as stored: two decimals, zero allowed, nothing negative or absurd."""
    rounded = cost.quantize(CENTS, rounding=ROUND_HALF_EVEN) if cost.is_finite() else None
    if rounded is None or rounded < money.ZERO or rounded >= LIMIT:
        raise DomainError(COST_INVALID)
    return rounded


def _stored_cost(db: Session, menu_id: str) -> Decimal | None:
    """The fixed cost as the database holds it, read under a row lock that both writers of a menu's cost source take first.

    Two saves at once queue here instead of leaving two sources; the column is read, not the loaded object, so edits not yet flushed stay.
    """
    stored = db.scalar(select(MenuItem.fixed_cost).where(MenuItem.id == menu_id).with_for_update())
    return None if stored is None else Decimal(str(stored))


def ensure_no_fixed_cost(db: Session, menu_id: str) -> None:
    """Called before a menu recipe is written."""
    if _stored_cost(db, menu_id) is not None:
        raise DomainError(HAS_FIXED_COST)


def ensure_can_hold_stock(db: Session, menu_id: str) -> None:
    """Called before a menu is first marked as a counted item."""
    if _stored_cost(db, menu_id) is not None:
        raise DomainError(STOCK_HAS_FIXED_COST)


def of_menus(db: Session, outlet_id: str, menu_ids: list[str]) -> dict[str, Decimal]:
    """{menu id: cost at this branch} for the menus that have a fixed cost; two queries however many menus."""
    if not menu_ids:
        return {}
    base = {menu_id: Decimal(str(cost)) for menu_id, cost in db.execute(select(MenuItem.id, MenuItem.fixed_cost).where(MenuItem.id.in_(menu_ids), MenuItem.fixed_cost.is_not(None))).all()}
    if not base:
        return {}
    for menu_id, cost in db.execute(select(MenuOutletCost.menu_item_id, MenuOutletCost.cost).where(MenuOutletCost.outlet_id == outlet_id, MenuOutletCost.menu_item_id.in_(list(base)))).all():
        base[menu_id] = Decimal(str(cost))
    return base


def of_menus_many(db: Session, outlet_ids: list[str], menu_ids: list[str]) -> dict[tuple[str, str], Decimal]:
    """The same keyed by (branch, menu), for screens that look at several branches at once."""
    if not outlet_ids or not menu_ids:
        return {}
    base = {menu_id: Decimal(str(cost)) for menu_id, cost in db.execute(select(MenuItem.id, MenuItem.fixed_cost).where(MenuItem.id.in_(menu_ids), MenuItem.fixed_cost.is_not(None))).all()}
    if not base:
        return {}
    result = {(outlet_id, menu_id): cost for outlet_id in outlet_ids for menu_id, cost in base.items()}
    for outlet_id, menu_id, cost in db.execute(
        select(MenuOutletCost.outlet_id, MenuOutletCost.menu_item_id, MenuOutletCost.cost).where(MenuOutletCost.outlet_id.in_(outlet_ids), MenuOutletCost.menu_item_id.in_(list(base)))
    ).all():
        result[(outlet_id, menu_id)] = Decimal(str(cost))
    return result


def branch_costs(db: Session, menu_ids: list[str]) -> dict[str, dict[str, Decimal]]:
    """{menu id: {branch id: cost}} of the overrides, in one query."""
    if not menu_ids:
        return {}
    result: dict[str, dict[str, Decimal]] = {}
    for row in db.scalars(select(MenuOutletCost).where(MenuOutletCost.menu_item_id.in_(menu_ids))).all():
        result.setdefault(row.menu_item_id, {})[row.outlet_id] = Decimal(str(row.cost))
    return result


def save(db: Session, item: MenuItem, cost: Decimal | None, overrides: dict[str, Decimal | None] | None) -> bool:
    """Sets or clears the fixed cost and the branch overrides; True when something changed, so the caller can log it; does not commit.

    A figure keeps a branch cost, None removes it so the branch follows the base cost, and branches left out stay.
    Clearing the base removes every override with it, so none is left behind to come back later.
    """
    stored = _stored_cost(db, item.id)
    changed = False
    if cost is not None:
        figure = checked(cost)
        if stored is None:
            if db.scalar(select(exists().where(RecipeIngredient.menu_item_id == item.id))):
                raise DomainError(HAS_RECIPE)
            if db.scalar(select(exists().where(StockItem.menu_item_id == item.id))):
                raise DomainError(HAS_STOCK)
        if stored != figure:
            item.fixed_cost = figure
            changed = True
    if overrides:
        if stored is None and cost is None:
            raise DomainError(BRANCH_COST_WITHOUT_BASE)
        changed = _save_overrides(db, item, overrides) or changed
    return changed


def clear(db: Session, item: MenuItem) -> bool:
    """Back to a recipe or tracked stock: the base cost and every branch override go together; does not commit."""
    if _stored_cost(db, item.id) is None:
        return False
    item.fixed_cost = None
    db.execute(delete(MenuOutletCost).where(MenuOutletCost.menu_item_id == item.id))
    return True


def _save_overrides(db: Session, item: MenuItem, overrides: dict[str, Decimal | None]) -> bool:
    known = set(db.scalars(select(Outlet.id).where(Outlet.id.in_(list(overrides)))).all())
    if set(overrides) - known:
        raise DomainError(BRANCH_UNKNOWN)
    current = {row.outlet_id: row for row in db.scalars(select(MenuOutletCost).where(MenuOutletCost.menu_item_id == item.id)).all()}
    changed = False
    for outlet_id, value in overrides.items():
        row = current.get(outlet_id)
        if value is None:
            if row is not None:
                db.delete(row)
                changed = True
            continue
        figure = checked(value)
        if row is None:
            db.add(MenuOutletCost(menu_item_id=item.id, outlet_id=outlet_id, cost=figure))
            changed = True
        elif Decimal(str(row.cost)) != figure:
            row.cost = figure
            changed = True
    return changed
