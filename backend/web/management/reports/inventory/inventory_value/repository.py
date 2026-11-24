"""Database reads of the inventory value."""
from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.core.stock_balances import last_move_of
from app.models.ingredient import Ingredient
from app.core.branches import branch_filter


def balances_with_last_movement(db: Session, outlet_id: str | None) -> list[Row]:
    """(id, unit price, balance, last movement) of every ingredient, including those without cards."""
    return list(
        db.execute(
            select(Ingredient.id, Ingredient.unit_price, Ingredient.balance, last_move_of(Ingredient.id)).where(*branch_filter(Ingredient.outlet_id, outlet_id))
        ).all()
    )
