"""Reads and plain writes of closed stock counts; no rule lives here."""

from datetime import date

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.ingredient import Ingredient, IngredientCard, IngredientCount, IngredientCountChange, IngredientCountLine
from app.models.user import User
from app.core.branches import branch_filter
from app.core.sorting import SqlSorting


def find_ingredient(db: Session, ingredient_id: str, outlet_id: str) -> Ingredient | None:
    row = db.get(Ingredient, ingredient_id)
    return row if row is not None and row.outlet_id == outlet_id else None


def list_counts(db: Session, outlet_id: str | None, sort: str | None, limit: int, source: str | None = None) -> list[tuple[IngredientCount, str | None, int]]:
    lines = select(IngredientCountLine.count_id, func.count().label("total")).group_by(IngredientCountLine.count_id).subquery()
    user_name = func.coalesce(User.name, User.username)
    sorting = SqlSorting(
        columns={"period": IngredientCount.period_end, "user": user_name, "ingredients": func.coalesce(lines.c.total, 0), "closed_at": IngredientCount.created_at},
        default=(IngredientCount.period_end.desc(), IngredientCount.created_at.desc()),
        tiebreak=IngredientCount.id,
    )
    rows = db.execute(
        select(IngredientCount, func.coalesce(User.name, User.username), func.coalesce(lines.c.total, 0))
        .outerjoin(User, User.id == IngredientCount.user_id)
        .outerjoin(lines, lines.c.count_id == IngredientCount.id)
        .where(*branch_filter(IngredientCount.outlet_id, outlet_id), *([IngredientCount.source == source] if source else []))
        .order_by(*sorting.order_by(sort))
        .limit(limit)
    ).all()
    return [(count, name, total) for count, name, total in rows]


def summary_of(db: Session, count_id: str) -> tuple[IngredientCount, str | None, int] | None:
    total = select(func.count()).select_from(IngredientCountLine).where(IngredientCountLine.count_id == IngredientCount.id).scalar_subquery()
    row = db.execute(
        select(IngredientCount, func.coalesce(User.name, User.username), total)
        .outerjoin(User, User.id == IngredientCount.user_id)
        .where(IngredientCount.id == count_id)
    ).first()
    return (row[0], row[1], row[2]) if row else None


def counts_before(db: Session, outlet_id: str, start: date) -> list[IngredientCount]:
    return list(db.scalars(select(IngredientCount).where(IngredientCount.outlet_id == outlet_id, IngredientCount.period_end < start)).all())


def find(db: Session, count_id: str) -> IngredientCount | None:
    return db.get(IngredientCount, count_id)


def lines_of(db: Session, count_id: str, ingredient_ids: list[str]) -> dict[str, IngredientCountLine]:
    rows = db.scalars(select(IngredientCountLine).where(IngredientCountLine.count_id == count_id, IngredientCountLine.ingredient_id.in_(ingredient_ids)))
    return {line.ingredient_id: line for line in rows if line.ingredient_id}


CHANGE_SORTING = SqlSorting(
    columns={"time": IngredientCountChange.created_at, "ingredient": IngredientCountChange.ingredient_name, "user": func.coalesce(User.name, User.username)},
    default=(IngredientCountChange.created_at.desc(),),
    tiebreak=IngredientCountChange.id,
)


def changes_page(db: Session, count_id: str, sort: str | None, page: int, size: int) -> tuple[list[tuple[IngredientCountChange, str | None]], int]:
    where = IngredientCountChange.count_id == count_id
    total = db.scalar(select(func.count()).select_from(IngredientCountChange).where(where)) or 0
    rows = db.execute(
        select(IngredientCountChange, func.coalesce(User.name, User.username))
        .outerjoin(User, User.id == IngredientCountChange.user_id)
        .where(where)
        .order_by(*CHANGE_SORTING.order_by(sort))
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return [(change, name) for change, name in rows], total


def delete_count(db: Session, count: IngredientCount) -> None:
    """The adjustment cards born from this count go with it, so the balance returns to what it was before the period was closed."""
    db.execute(delete(IngredientCard).where(IngredientCard.count_id == count.id))
    db.execute(delete(IngredientCountLine).where(IngredientCountLine.count_id == count.id))
    db.delete(count)
