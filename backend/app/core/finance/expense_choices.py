"""What the expense form offers to pick from: the branch's ingredients for a line, and every active employee as the buyer."""
from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.search import contains
from app.models.category import Unit
from app.models.ingredient import Ingredient
from app.models.outlet import Outlet
from app.models.user import User


@dataclass(frozen=True)
class IngredientChoice:
    id: str
    name: str
    unit_id: str | None
    unit_name: str | None


@dataclass(frozen=True)
class BuyerChoice:
    id: str
    name: str
    outlet_name: str | None


def ingredients(db: Session, outlet_id: str, search: str | None, size: int, page: int = 1) -> list[IngredientChoice]:
    """Active ingredients of the expense's branch only, the same ones a receipt line is matched against, one page at a time."""
    filters = [Ingredient.outlet_id == outlet_id, Ingredient.is_active.is_(True)]
    if search:
        filters.append(contains(Ingredient.name, search))
    rows = db.execute(
        select(Ingredient.id, Ingredient.name, Ingredient.unit_id, Unit.name)
        .outerjoin(Unit, Unit.id == Ingredient.unit_id)
        .where(*filters)
        .order_by(Ingredient.name, Ingredient.id)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return [IngredientChoice(*row) for row in rows]


def buyers(db: Session, search: str | None, size: int, page: int = 1) -> list[BuyerChoice]:
    """Any branch may do the shopping, so every active employee is offered; the branch tells two of the same name apart."""
    filters = [User.is_active.is_(True)]
    if search:
        filters.append(or_(contains(User.name, search), contains(User.username, search)))
    rows = db.execute(
        select(User.id, User.name, User.username, Outlet.name)
        .outerjoin(Outlet, Outlet.id == User.outlet_id)
        .where(*filters)
        .order_by(User.name, User.username, User.id)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return [BuyerChoice(id=id_, name=name or username, outlet_name=outlet) for id_, name, username, outlet in rows]
