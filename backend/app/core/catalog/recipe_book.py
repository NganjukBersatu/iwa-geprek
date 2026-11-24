"""Master Resep as the web and the tablet read and save it; recipe writing lives in app.core.catalog.recipes and costing in recipe_costing."""
from decimal import Decimal

from sqlalchemy import exists, func, or_, select, true
from sqlalchemy.orm import Session

from app.core.auth import AnyOf
from app.core.catalog import recipe_costing, recipes
from app.core.errors import DomainError
from app.core.money import decimal_of
from app.core.orders.recipes import cost_of, of_menus_many
from app.core.pricing import price_map_many
from app.core.search import contains
from app.models.cafe_settings import CafeSettings
from app.models.category import Category, Unit
from app.models.ingredient import Ingredient, RecipeIngredient
from app.models.menu_item import MenuItem
from app.models.outlet import Outlet
from app.models.user import User
from app.core.catalog.recipe_schemas import (
    IngredientOptionOut,
    CopiedIngredientOut,
    RecipeLineOut,
    RecipeOut,
    RecipeSaveIn,
    RecipeSaveOut,
)

PERMISSION_COST = "resep.detail"
PERMISSION_LEARN = "resep"
PERMISSION_MANAGE = "resep.kelola"
# Either key opens Master Resep; only the cost key also shows cost figures.
READ_GATE = AnyOf((PERMISSION_COST, PERMISSION_LEARN))
WITH_RECIPE = "ada"
NOT_FOUND = 404
CENTS = Decimal("0.01")
MENU_NOT_FOUND = "Menu tidak ditemukan."


def units_of(db: Session, ingredient_ids: set[str]) -> dict[str, str | None]:
    if not ingredient_ids:
        return {}
    rows = db.execute(select(Ingredient.id, Unit.name).outerjoin(Unit, Unit.id == Ingredient.unit_id).where(Ingredient.id.in_(ingredient_ids))).all()
    return dict(rows)


def _recipes(db: Session, user: User, outlet_id: str, menus: list[tuple[MenuItem, str | None]]) -> list[RecipeOut]:
    return _recipes_many(db, user, [(menu, name, outlet_id) for menu, name in menus])


def _recipes_many(db: Session, user: User, rows: list[tuple[MenuItem, str | None, str]]) -> list[RecipeOut]:
    """Margins use the selling price at the row's branch, since recipes are kept per branch and a branch price would make the base price misleading.

    Rows may belong to any number of branches: the recipes, prices, add costs, settings, branch names, and units are each read once for all of them.
    """
    if not rows:
        return []
    outlet_ids = sorted({outlet_id for _, _, outlet_id in rows})
    menus = list({menu.id: menu for menu, _, _ in rows}.values())
    menu_ids = [menu.id for menu in menus]
    lines = of_menus_many(db, outlet_ids, menu_ids)
    settings = {item.outlet_id: item for item in db.scalars(select(CafeSettings).where(CafeSettings.outlet_id.in_(outlet_ids))).all()}
    prices = price_map_many(db, outlet_ids, menus, settings)
    manual = recipe_costing.manual_of_many(db, outlet_ids, menu_ids)
    units = units_of(db, {line.ingredient_id for menu_lines in lines.values() for line in menu_lines})
    sees_cost = user.allows(PERMISSION_COST)
    outlet_names = dict(db.execute(select(Outlet.id, Outlet.name).where(Outlet.id.in_(outlet_ids))).all())
    result = []
    for menu, category_name, outlet_id in rows:
        key = (outlet_id, menu.id)
        menu_lines = sorted(lines.get(key, []), key=lambda line: line.ingredient_name.lower())
        figures = recipe_costing.costing(cost_of(menu_lines), prices[key], manual.get(key), settings.get(outlet_id))
        result.append(
            RecipeOut(
                outlet_id=outlet_id,
                outlet_name=outlet_names.get(outlet_id, ""),
                menu_id=menu.id,
                menu_name=menu.name,
                category_name=category_name,
                price=prices[key],
                has_recipe=bool(menu_lines),
                lines=[
                    RecipeLineOut(
                        ingredient_id=line.ingredient_id,
                        ingredient_name=line.ingredient_name,
                        unit=units.get(line.ingredient_id),
                        qty=line.qty,
                        unit_price=line.unit_price if sees_cost else None,
                        cost=(line.qty * line.unit_price).quantize(CENTS) if sees_cost else None,
                    )
                    for line in menu_lines
                ],
                # Someone who may only learn the recipe sees ingredients and amounts, never a cost figure.
                ingredients_cost=figures.ingredients if sees_cost else None,
                add_cost_kind=figures.add_cost_kind if sees_cost else None,
                add_cost_value=figures.add_cost_value if sees_cost else None,
                add_cost_custom=figures.add_cost_custom,
                add_cost=figures.add_cost if sees_cost else None,
                overhead=figures.overhead if sees_cost else None,
                final_cost=figures.final_cost if sees_cost else None,
                margin=figures.margin if sees_cost else None,
                margin_percent=figures.margin_percent if sees_cost else None,
                target_margin_percent=figures.target_margin_percent if sees_cost else None,
                target_custom=figures.target_custom,
                suggested_price=figures.suggested_price if sees_cost else None,
            )
        )
    return result


def _menus(db: Session, menu_id: str | None = None) -> list[tuple[MenuItem, str | None]]:
    statement = select(MenuItem, Category.name).outerjoin(Category, Category.id == MenuItem.category_id)
    if menu_id:
        statement = statement.where(MenuItem.id == menu_id)
    rows = db.execute(statement.order_by(Category.name, MenuItem.name, MenuItem.id)).all()
    return [(menu, name) for menu, name in rows]


def list_recipes(db: Session, user: User, outlet_id: str | None, search: str | None, recipe: str | None, page: int, size: int, sort: str | None = None) -> tuple[list[RecipeOut], int]:
    """One page of the menus with their recipe at the branch, an empty one included, since the menu list is shared and recipes are not. No branch lists every active branch: one row per menu per branch."""
    statement = (
        select(MenuItem, Category.name, Outlet.id)
        .select_from(MenuItem)
        .outerjoin(Category, Category.id == MenuItem.category_id)
        .join(Outlet, true())
    )
    statement = statement.where(Outlet.id == outlet_id) if outlet_id else statement.where(Outlet.is_active.is_(True))
    if search:
        statement = statement.where(or_(contains(MenuItem.name, search), contains(Category.name, search)))
    if recipe:
        has = exists().where(RecipeIngredient.outlet_id == Outlet.id, RecipeIngredient.menu_item_id == MenuItem.id)
        statement = statement.where(has if recipe == WITH_RECIPE else ~has)
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    order = (Category.name, MenuItem.name, MenuItem.id, Outlet.name) if sort is None else ((MenuItem.name.desc() if sort.startswith("-") else MenuItem.name.asc()), MenuItem.id, Outlet.name)
    rows = db.execute(statement.order_by(*order).limit(size).offset((page - 1) * size)).all()
    return _recipes_many(db, user, [(menu, category_name, branch_id) for menu, category_name, branch_id in rows]), total


def recipe_of(db: Session, user: User, outlet_id: str, menu_id: str) -> RecipeOut:
    found = _menus(db, menu_id)
    if not found:
        raise DomainError(MENU_NOT_FOUND, status=NOT_FOUND)
    return _recipes(db, user, outlet_id, found)[0]


def save(db: Session, user: User, outlet_id: str, menu_id: str, body: RecipeSaveIn) -> RecipeSaveOut:
    if db.get(MenuItem, menu_id) is None:
        raise DomainError(MENU_NOT_FOUND, status=NOT_FOUND)
    lines = [recipes.RecipeInput(line.ingredient_id, line.qty) for line in body.lines]
    sent = body.model_fields_set
    values = body.model_dump(include={"add_cost_kind", "add_cost_value", "overhead", "target_margin_percent"})
    if body.all_branches:
        result = recipes.spread(db, recipes.KIND_MENU, menu_id, outlet_id, lines, user.locked_outlet_id)
        for branch_id in db.scalars(select(Outlet.id).where(Outlet.is_active.is_(True))).all():
            recipe_costing.save_manual(db, branch_id, menu_id, sent, values, not lines)
        branches = result.branches
        copied = [CopiedIngredientOut(branch_name=item.branch_name, ingredient_name=item.ingredient_name) for item in result.copied]
    else:
        recipes.checked_lines(db, outlet_id, lines)
        recipes.replace(db, recipes.KIND_MENU, menu_id, outlet_id, lines)
        recipe_costing.save_manual(db, outlet_id, menu_id, sent, values, not lines)
        branches, copied = 1, []
    db.commit()
    return RecipeSaveOut(recipe=recipe_of(db, user, outlet_id, menu_id), branches=branches, copied=copied)


# Batas pilihan bahan resep per permintaan dan panjang kata cari, sama untuk web dan tablet.
OPTION_MAX_SIZE = 100
OPTION_MAX_SEARCH = 100


def ingredient_options(
    db: Session, user: User, outlet_id: str, search: str | None = None, page: int = 1, size: int | None = None
) -> list[IngredientOptionOut]:
    """Active ingredients of the branch to pick from, searched and one page at a time; prices only for those who may see costs."""
    sees_cost = user.allows(PERMISSION_COST)
    filters = [Ingredient.outlet_id == outlet_id, Ingredient.is_active.is_(True)]
    if search:
        filters.append(contains(Ingredient.name, search))
    statement = select(Ingredient, Unit.name).outerjoin(Unit, Unit.id == Ingredient.unit_id).where(*filters).order_by(Ingredient.name, Ingredient.id)
    # Tanpa size hanya untuk APK dan tab web sebelum 8 Nov 2026 yang memuat semua bahan; hapus setelah MIN_VERSION_APK melewati rilis itu.
    if size is not None:
        statement = statement.offset((page - 1) * size).limit(size)
    rows = db.execute(statement).all()
    return [
        IngredientOptionOut(id=item.id, name=item.name, unit=unit, unit_price=decimal_of(item.unit_price) if sees_cost else None)
        for item, unit in rows
    ]
