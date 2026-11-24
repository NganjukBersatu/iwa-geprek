"""Variant groups and extras of the management web; every rule lives in app.core.catalog.options and recipes."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.catalog import options, recipes
from app.core.catalog.recipe_schemas import CopiedIngredientOut
from app.core.orders.recipes import RecipeLine, of_options
from app.models.category import Category, Unit
from app.models.extra import Extra
from app.models.ingredient import Ingredient
from app.models.user import User
from app.models.variant import VariantGroup
from web.management.options.schemas import (
    VariantChoiceOut,
    ExtraCategoryOut,
    ManagedExtraOut,
    OptionRecipeIn,
    OptionRecipeLineOut,
    OptionRecipeOut,
    ManagedVariantGroupOut,
)


def _units(db: Session, lines: list[RecipeLine]) -> dict[str, str | None]:
    ids = {line.ingredient_id for line in lines}
    if not ids:
        return {}
    return dict(db.execute(select(Ingredient.id, Unit.name).outerjoin(Unit, Unit.id == Ingredient.unit_id).where(Ingredient.id.in_(ids))).all())


def _recipe_out(lines: list[RecipeLine], units: dict[str, str | None]) -> list[OptionRecipeLineOut]:
    return [
        OptionRecipeLineOut(ingredient_id=line.ingredient_id, ingredient_name=line.ingredient_name, unit=units.get(line.ingredient_id), qty=line.qty)
        for line in sorted(lines, key=lambda line: line.ingredient_name.lower())
    ]


def groups(db: Session, outlet_id: str | None, only: list[VariantGroup] | None = None) -> list[ManagedVariantGroupOut]:
    """Recipes are shown for the chosen branch; without one, every recipe list is empty."""
    found = only if only is not None else list(db.scalars(select(VariantGroup).order_by(VariantGroup.position, VariantGroup.name)).all())
    choices = options.choices_of(db, [group.id for group in found])
    choice_ids = [choice.id for group_choices in choices.values() for choice in group_choices]
    lines = of_options(db, recipes.KIND_VARIANT, choice_ids, outlet_id) if outlet_id else {}
    units = _units(db, [line for owner in lines.values() for line in owner])
    menus = options.menus_of(db, "varian", [group.id for group in found])
    return [
        ManagedVariantGroupOut(
            id=group.id,
            name=group.name,
            required=group.required,
            is_active=group.is_active,
            choices=[
                VariantChoiceOut(id=choice.id, name=choice.name, color=choice.color, is_active=choice.is_active, recipe=_recipe_out(lines.get(choice.id, []), units))
                for choice in choices.get(group.id, [])
            ],
            menu_ids=menus.get(group.id, []),
            outlet_id=group.outlet_id,
        )
        for group in found
    ]


def extras(db: Session, outlet_id: str | None, only: list[Extra] | None = None) -> list[ManagedExtraOut]:
    found = only if only is not None else list(db.scalars(select(Extra).order_by(Extra.position, Extra.name)).all())
    ids = [extra.id for extra in found]
    prices = options.branch_prices_of(db, ids)
    menus = options.menus_of(db, "ekstra", ids)
    lines = of_options(db, recipes.KIND_EXTRA, ids, outlet_id) if outlet_id else {}
    units = _units(db, [line for owner in lines.values() for line in owner])
    category_ids = {extra.category_id for extra in found if extra.category_id}
    names = dict(db.execute(select(Category.id, Category.name).where(Category.id.in_(category_ids))).all()) if category_ids else {}
    return [
        ManagedExtraOut(
            id=extra.id,
            name=extra.name,
            price=extra.price,
            is_active=extra.is_active,
            outlet_ids=extra.outlet_ids,
            branch_prices=prices.get(extra.id, {}),
            category_id=extra.category_id,
            category_name=names.get(extra.category_id),
            menu_ids=menus.get(extra.id, []),
            recipe=_recipe_out(lines.get(extra.id, []), units),
        )
        for extra in found
    ]


def extra_categories(db: Session) -> list[ExtraCategoryOut]:
    rows = db.scalars(select(Category).where(Category.kind == options.EXTRA_CATEGORY_KIND).order_by(Category.name)).all()
    return [ExtraCategoryOut(id=row.id, name=row.name) for row in rows]


def save_recipe(db: Session, user: User, kind: str, owner_id: str, outlet_id: str, body: OptionRecipeIn) -> OptionRecipeOut:
    lines = [recipes.RecipeInput(line.ingredient_id, line.qty) for line in body.lines]
    if body.all_branches:
        result = recipes.spread(db, kind, owner_id, outlet_id, lines, user.locked_outlet_id)
        branches = result.branches
        copied = [CopiedIngredientOut(branch_name=item.branch_name, ingredient_name=item.ingredient_name) for item in result.copied]
    else:
        recipes.checked_lines(db, outlet_id, lines)
        recipes.replace(db, kind, owner_id, outlet_id, lines)
        branches, copied = 1, []
    db.commit()
    saved = of_options(db, kind, [owner_id], outlet_id).get(owner_id, [])
    return OptionRecipeOut(recipe=_recipe_out(saved, _units(db, saved)), branches=branches, copied=copied)
