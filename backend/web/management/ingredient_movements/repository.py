"""Reads of the ingredient ledger; no rule lives here."""
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.search import contains
from app.models.category import Unit
from app.core.ingredients.ledger import manual_use_clause
from app.models.ingredient import INGREDIENT_WASTE, Ingredient, IngredientCard
from app.models.user import User
from app.core.ingredients.causes import HUMAN_ERROR_CODES
from app.core.business_days import ingredient_cards_in
from app.core.sorting import SqlSorting

USE_KIND = "use"

SORTING = SqlSorting(
    columns={
        "ingredient": IngredientCard.ingredient_name,
        "business_day": IngredientCard.business_day,
        "created_at": IngredientCard.created_at,
        "qty": func.abs(IngredientCard.qty),
        "cause": IngredientCard.cause,
        "user": func.coalesce(User.name, User.username),
    },
    default=(IngredientCard.business_day.desc(), IngredientCard.created_at.desc()),
    tiebreak=IngredientCard.id,
)


def page_of(
    db: Session, start: date, end: date, outlet_id: str | None, kind: str | None, search: str | None, sort: str | None, page: int, size: int
) -> tuple[list[tuple[IngredientCard, str | None, str | None]], int, int, int]:
    filters = [
        *ingredient_cards_in(start, end, outlet_id),
    ]
    if kind == USE_KIND:
        filters.append(manual_use_clause())
    elif kind:
        filters.append(IngredientCard.kind == kind)
    if search:
        filters.append(or_(contains(IngredientCard.ingredient_name, search), contains(IngredientCard.note, search)))
    total = db.scalar(select(func.count()).select_from(IngredientCard).where(*filters)) or 0
    count = lambda *extra: db.scalar(select(func.count()).select_from(IngredientCard).where(*filters, *extra)) or 0  # noqa: E731
    human = count(IngredientCard.kind == INGREDIENT_WASTE, IngredientCard.cause.in_(HUMAN_ERROR_CODES))
    natural = count(IngredientCard.kind == INGREDIENT_WASTE, IngredientCard.cause.is_not(None), IngredientCard.cause.not_in(HUMAN_ERROR_CODES))
    rows = db.execute(
        select(IngredientCard, func.coalesce(User.name, User.username), Unit.name)
        .outerjoin(User, User.id == IngredientCard.user_id)
        .outerjoin(Ingredient, Ingredient.id == IngredientCard.ingredient_id)
        .outerjoin(Unit, Unit.id == Ingredient.unit_id)
        .where(*filters)
        .order_by(*SORTING.order_by(sort))
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return [(card, name, unit) for card, name, unit in rows], total, human, natural


def with_user(db: Session, card_id: str) -> tuple[IngredientCard, str | None, str | None] | None:
    row = db.execute(
        select(IngredientCard, func.coalesce(User.name, User.username), Unit.name)
        .outerjoin(User, User.id == IngredientCard.user_id)
        .outerjoin(Ingredient, Ingredient.id == IngredientCard.ingredient_id)
        .outerjoin(Unit, Unit.id == Ingredient.unit_id)
        .where(IngredientCard.id == card_id)
    ).first()
    return (row[0], row[1], row[2]) if row else None


def find_card(db: Session, card_id: str) -> IngredientCard | None:
    return db.get(IngredientCard, card_id)
