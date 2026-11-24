"""Database reads of the turnover report."""
from datetime import date

from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.models.category import Category, Unit
from app.core.branches import branch_filter
from app.core.stock_balances import last_move_of
from app.models.ingredient import Ingredient


def ingredient_names(db: Session, outlet_id: str | None) -> list[Row]:
    """(id, name, category name, unit name, unit price) in database order."""
    return list(
        db.execute(
            select(Ingredient.id, Ingredient.name, Category.name, Unit.name, Ingredient.unit_price)
            .outerjoin(Category, Category.id == Ingredient.category_id)
            .outerjoin(Unit, Unit.id == Ingredient.unit_id)
            .where(*branch_filter(Ingredient.outlet_id, outlet_id))
        ).all()
    )


def last_movements(db: Session, outlet_id: str | None) -> dict[str, date]:
    """One index lookup per ingredient, however long its history."""
    rows = db.execute(select(Ingredient.id, last_move_of(Ingredient.id)).where(*branch_filter(Ingredient.outlet_id, outlet_id)))
    return {ingredient_id: moved for ingredient_id, moved in rows if moved is not None}
