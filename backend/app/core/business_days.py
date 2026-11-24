"""Which business day a money or stock row belongs to is stored on the row by the database; every reader filters and groups on it here."""
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.branches import branch_filter
from app.core.clock import today
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.expense import Expense
from app.models.ingredient import IngredientCard
from app.models.order import Order
from app.models.overpayment import Overpayment
from app.models.stock import StockCard


def within(column, start: date, end: date) -> tuple:
    return (column >= start, column <= end)


def first_unfinished_day(db: Session, outlet_ids: list[str]) -> dict[str, date]:
    """Per branch, the first business day that may still change: the oldest running session's, else today."""
    running = dict(
        db.execute(
            select(CashSession.outlet_id, func.min(CashSession.business_day))
            .where(CashSession.status == CashSessionStatus.OPEN, CashSession.outlet_id.in_(outlet_ids))
            .group_by(CashSession.outlet_id)
        ).all()
    )
    current = today()
    return {outlet_id: min(running.get(outlet_id, current), current) for outlet_id in outlet_ids}


def day_opening(db: Session, day: date, outlet_id: str | None) -> datetime | None:
    """When the first session of a business day opened; the day's own clock starts there, not at calendar midnight."""
    return db.execute(select(func.min(CashSession.opened_at)).where(*sessions_in(day, day, outlet_id))).scalar()


def orders_in(start: date, end: date, outlet_id: str | None) -> tuple:
    return (*within(Order.business_day, start, end), *branch_filter(Order.outlet_id, outlet_id))


def valid_orders_in(start: date, end: date, outlet_id: str | None) -> tuple:
    """Voided orders never become revenue; their money went back to the customer."""
    return (*orders_in(start, end, outlet_id), Order.voided_at.is_(None))


def expenses_in(start: date, end: date, outlet_id: str | None) -> tuple:
    return (*within(Expense.business_day, start, end), *branch_filter(Expense.outlet_id, outlet_id))


def sessions_in(start: date, end: date, outlet_id: str | None) -> tuple:
    return (*within(CashSession.business_day, start, end), *branch_filter(CashSession.outlet_id, outlet_id))


def overpayments_in(start: date, end: date, outlet_id: str | None) -> tuple:
    return (*within(Overpayment.business_day, start, end), *branch_filter(Overpayment.outlet_id, outlet_id))


def ingredient_cards_in(start: date, end: date, outlet_id: str | None) -> tuple:
    return (*within(IngredientCard.business_day, start, end), *branch_filter(IngredientCard.outlet_id, outlet_id))


def stock_cards_in(start: date, end: date, outlet_id: str | None) -> tuple:
    return (*within(StockCard.business_day, start, end), *branch_filter(StockCard.outlet_id, outlet_id))
