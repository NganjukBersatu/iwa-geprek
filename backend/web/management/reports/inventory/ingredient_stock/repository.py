"""Database reads of the ingredient stock report."""
from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.models.category import Category, Unit
from app.models.ingredient import Ingredient, IngredientCount, IngredientCountLine
from app.core.branches import branch_filter


def ingredients_by_category(db: Session, outlet_id: str | None) -> list[Row]:
    """(ingredient, category name, unit name), ordered by category then name."""
    return list(
        db.execute(
            select(Ingredient, Category.name, Unit.name)
            .outerjoin(Category, Category.id == Ingredient.category_id)
            .outerjoin(Unit, Unit.id == Ingredient.unit_id)
            .where(*branch_filter(Ingredient.outlet_id, outlet_id))
            .order_by(Category.name, Ingredient.name)
        ).all()
    )


def counts_for_period(db: Session, outlet_id: str | None, start, end) -> list[IngredientCount]:
    """Counts closed for exactly this period; more than one only when every branch is combined."""
    return list(
        db.scalars(
            select(IngredientCount).where(
                IngredientCount.period_start == start,
                IngredientCount.period_end == end,
                *branch_filter(IngredientCount.outlet_id, outlet_id),
            )
        ).all()
    )


def count_lines(db: Session, count_ids: list[str]) -> list[IngredientCountLine]:
    if not count_ids:
        return []
    return list(db.scalars(select(IngredientCountLine).where(IngredientCountLine.count_id.in_(count_ids))).all())
