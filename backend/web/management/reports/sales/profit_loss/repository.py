"""Database reads of the profit and loss report; every aggregate passes through branch_filter."""
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.money import decimal_of
from app.models.expense import Expense
from app.models.ingredient import (
    INGREDIENT_RND,
    INGREDIENT_WASTE,
    Ingredient,
    IngredientCard,
    IngredientCount,
    IngredientCountLine,
)
from app.models.order import Order
from app.models.order_item import OrderItem
from app.core.branches import branch_filter
from app.core.business_days import expenses_in, ingredient_cards_in, valid_orders_in
from web.management.reports.menu import sold_orders
from web.management.reports.sales.profit_loss.constants import ITEMS_WITHOUT_COST_LIMIT


def revenue_and_count(db: Session, start: date, end: date, outlet_id: str | None) -> tuple[Decimal, int]:
    total, count = db.execute(
        select(func.coalesce(func.sum(Order.total), 0), func.count()).where(*valid_orders_in(start, end, outlet_id))
    ).one()
    return decimal_of(total), int(count or 0)


def cost_of_goods(db: Session, start: date, end: date, outlet_id: str | None) -> tuple[Decimal, int, int]:
    """Sum of unit cost x qty over lines that have a cost, all line count, and costed line count."""
    has_cost = OrderItem.unit_cost.is_not(None)
    cost, lines, costed = db.execute(
        select(
            func.coalesce(func.sum(case((has_cost, OrderItem.unit_cost * OrderItem.qty), else_=0)), 0),
            func.count(),
            func.coalesce(func.sum(case((has_cost, 1), else_=0)), 0),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(*valid_orders_in(start, end, outlet_id))
    ).one()
    return decimal_of(cost), int(lines or 0), int(costed or 0)


def orders_without_lines(db: Session, start: date, end: date, outlet_id: str | None) -> tuple[int, Decimal]:
    """Orders with no line have no cost to subtract, so their whole total would read as profit."""
    return sold_orders.orders_without_lines(db, valid_orders_in(start, end, outlet_id))


def items_without_cost(db: Session, start: date, end: date, outlet_id: str | None) -> list[str]:
    return list(
        db.scalars(
            select(OrderItem.menu_item_name)
            .join(Order, Order.id == OrderItem.order_id)
            .where(*valid_orders_in(start, end, outlet_id), OrderItem.unit_cost.is_(None))
            .group_by(OrderItem.menu_item_name)
            .order_by(func.sum(OrderItem.qty).desc())
            .limit(ITEMS_WITHOUT_COST_LIMIT)
        ).all()
    )


def ingredient_losses(db: Session, start: date, end: date, outlet_id: str | None) -> dict[str, Decimal]:
    """Waste and R&D outflow by kind, valued at today's unit price."""
    return dict(
        db.execute(
            select(
                IngredientCard.kind,
                func.coalesce(func.sum(-IngredientCard.qty * Ingredient.unit_price), 0),
            )
            .join(Ingredient, Ingredient.id == IngredientCard.ingredient_id)
            .where(
                *ingredient_cards_in(start, end, outlet_id),
                IngredientCard.kind.in_([INGREDIENT_WASTE, INGREDIENT_RND]),
            )
            .group_by(IngredientCard.kind)
        ).all()
    )


def count_difference(db: Session, start: date, end: date, outlet_id: str | None) -> Decimal:
    """Stock-take shortfall of the periods closed within the range, from their snapshot."""
    return decimal_of(
        db.scalar(
            select(
                func.coalesce(
                    func.sum((IngredientCountLine.book_balance - IngredientCountLine.counted) * IngredientCountLine.value),
                    0,
                )
            )
            .join(IngredientCount, IngredientCount.id == IngredientCountLine.count_id)
            .where(
                IngredientCount.period_end >= start,
                IngredientCount.period_end <= end,
                *branch_filter(IngredientCount.outlet_id, outlet_id),
            )
        )
    )


def split_expenses(db: Session, start: date, end: date, outlet_id: str | None) -> tuple[Decimal, Decimal]:
    """Operating expenses and ingredient purchases, told apart by a card linked to the expense."""
    is_purchase = select(1).where(IngredientCard.expense_id == Expense.id).exists()
    in_range = expenses_in(start, end, outlet_id)
    operating = decimal_of(db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(*in_range, ~is_purchase)))
    purchases = decimal_of(db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(*in_range, is_purchase)))
    return operating, purchases
