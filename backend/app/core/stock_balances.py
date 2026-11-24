"""Stock balances kept on the row by database triggers (bahan.saldo, stok_item.saldo), and the one place that reads them.

Reading: the balance now, and the balance before a business day as that balance minus what moved on it and after, so no read sums a whole history.
Writing: every card write first locks the balance rows it will move, always in the same order, so two sales sharing an
ingredient queue behind each other instead of locking each other out.
"""
from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import ColumnElement, event, func, select, tuple_
from sqlalchemy.orm import ORMExecuteState, Session
from sqlalchemy.sql.selectable import ScalarSelect

from app.core.clock import today
from app.core.money import decimal_of
from app.models.ingredient import Ingredient, IngredientCard
from app.models.stock import StockCard, StockItem


def last_move_of(ingredient_id: ColumnElement[str]) -> ScalarSelect:
    """The business day of an ingredient's newest card, read from the end of ix_kartu_bahan_bahan_business_day."""
    return select(func.max(IngredientCard.business_day)).where(IngredientCard.ingredient_id == ingredient_id).scalar_subquery()


def idle_days(last_move: date | None) -> int | None:
    """Whole business days since the last movement; None when it never moved."""
    return (today() - last_move).days if last_move is not None else None


def balance_before(db: Session, ingredient_id: str, day: date) -> Decimal:
    moved = select(func.coalesce(func.sum(IngredientCard.qty), 0)).where(IngredientCard.ingredient_id == ingredient_id, IngredientCard.business_day >= day)
    row = db.execute(select(Ingredient.balance, moved.scalar_subquery()).where(Ingredient.id == ingredient_id)).one_or_none()
    return decimal_of(row[0]) - decimal_of(row[1]) if row else Decimal(0)


def balances_before(db: Session, outlet_id: str | None, day: date) -> dict[str, Decimal]:
    """Every ingredient of the branch, or of every branch when none is given."""
    moved = (
        select(IngredientCard.ingredient_id, func.sum(IngredientCard.qty).label("qty"))
        .where(IngredientCard.business_day >= day, IngredientCard.ingredient_id.is_not(None))
        .group_by(IngredientCard.ingredient_id)
    )
    ingredients = select(Ingredient.id, Ingredient.balance)
    if outlet_id:
        moved = moved.where(IngredientCard.outlet_id == outlet_id)
        ingredients = ingredients.where(Ingredient.outlet_id == outlet_id)
    since = moved.subquery()
    rows = db.execute(ingredients.add_columns(since.c.qty).outerjoin(since, since.c.ingredient_id == Ingredient.id)).all()
    return {ingredient_id: decimal_of(balance) - decimal_of(qty) for ingredient_id, balance, qty in rows}


def hold(db: Session, ingredient_ids: Iterable[str | None], stock_keys: Iterable[tuple[str, str | None]]) -> None:
    """Locks the balance rows a write is about to move: ingredients by id, then resold items by branch and menu."""
    ids = sorted({ingredient_id for ingredient_id in ingredient_ids if ingredient_id})
    keys = sorted({(outlet_id, menu_id) for outlet_id, menu_id in stock_keys if menu_id})
    with db.no_autoflush:
        if ids:
            db.execute(select(Ingredient.id).where(Ingredient.id.in_(ids)).order_by(Ingredient.id).with_for_update())
        if keys:
            db.execute(
                select(StockItem.id)
                .where(tuple_(StockItem.outlet_id, StockItem.menu_item_id).in_(keys))
                .order_by(StockItem.outlet_id, StockItem.menu_item_id)
                .with_for_update()
            )


def _before_flush(session: Session, *_: Any) -> None:
    changed = [*session.new, *session.dirty, *session.deleted]
    ingredient_ids = [card.ingredient_id for card in changed if isinstance(card, IngredientCard)]
    stock_keys = [(card.outlet_id, card.menu_item_id) for card in changed if isinstance(card, StockCard)]
    if ingredient_ids or stock_keys:
        hold(session, ingredient_ids, stock_keys)


def _before_statement(state: ORMExecuteState) -> None:
    """delete() and update() of cards skip the flush, so their rows are found and locked here first."""
    if not (state.is_delete or state.is_update):
        return
    table, where = state.statement.table, state.statement.whereclause
    if table is IngredientCard.__table__:
        found = select(IngredientCard.ingredient_id).distinct()
        hold(state.session, state.session.scalars(found.where(where) if where is not None else found).all(), [])
    elif table is StockCard.__table__:
        found = select(StockCard.outlet_id, StockCard.menu_item_id).distinct()
        hold(state.session, [], [tuple(row) for row in state.session.execute(found.where(where) if where is not None else found).all()])


def watch_card_writes() -> None:
    """Called at startup; a second call adds nothing."""
    if event.contains(Session, "before_flush", _before_flush):
        return
    event.listen(Session, "before_flush", _before_flush)
    event.listen(Session, "do_orm_execute", _before_statement)
