"""Reading expenses for any screen; who may see what is decided by the caller."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.branches import branch_filter
from app.core.business_days import expenses_in
from app.core.money import decimal_of
from app.core.search import contains
from app.core.sorting import SqlSorting
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.category import Unit
from app.models.expense import Expense, FundSource
from app.models.ingredient import Ingredient
from app.models.outlet import Outlet
from app.models.user import User


@dataclass(frozen=True)
class ExpenseRow:
    """One expense with the names every screen shows beside it."""

    expense: Expense
    username: str | None
    session_status: CashSessionStatus | None
    outlet_name: str | None
    ingredient_name: str | None
    unit_name: str | None


def _rows():
    return (
        select(Expense, User.username, CashSession.status, Outlet.name, Ingredient.name, Unit.name)
        .outerjoin(User, User.id == Expense.cashier_id)
        .outerjoin(CashSession, CashSession.id == Expense.cash_session_id)
        .outerjoin(Outlet, Outlet.id == Expense.outlet_id)
        .outerjoin(Ingredient, Ingredient.id == Expense.ingredient_id)
        .outerjoin(Unit, Unit.id == Expense.unit_id)
    )


SORTING = SqlSorting(
    columns={
        "item": Expense.item_name,
        "ingredient": Ingredient.name,
        "outlet": Outlet.name,
        "business_day": Expense.business_day,
        "created_at": Expense.created_at,
        "fund_source": Expense.fund_source,
        "recorder": User.username,
        "amount": Expense.amount,
    },
    default=(Expense.business_day.desc(), Expense.created_at.desc()),
    tiebreak=Expense.id,
)


def _row(found) -> ExpenseRow:
    return ExpenseRow(*found)


def page_of(
    db: Session,
    start: date,
    end: date,
    outlet_id: str | None,
    cashier_id: str | None,
    source: FundSource | None,
    search: str | None,
    sort: str | None,
    page: int,
    size: int,
    session_id: str | None = None,
) -> tuple[list[ExpenseRow], int, Decimal, Decimal]:
    # One session's expenses are all of them, whatever the dates; otherwise the range applies.
    if session_id:
        filters = [Expense.cash_session_id == session_id, *branch_filter(Expense.outlet_id, outlet_id)]
    else:
        filters = [*expenses_in(start, end, outlet_id)]
    if cashier_id:
        filters.append(Expense.cashier_id == cashier_id)
    if source:
        filters.append(Expense.fund_source == source)
    if search:
        filters.append(or_(contains(Expense.item_name, search), contains(Expense.note, search)))
    total = db.scalar(select(func.count()).select_from(Expense).where(*filters)) or 0
    total_amount = decimal_of(db.scalar(select(func.sum(Expense.amount)).where(*filters)))
    drawer_amount = decimal_of(db.scalar(select(func.sum(Expense.amount)).where(*filters, Expense.fund_source == FundSource.DRAWER_CASH)))
    rows = db.execute(
        _rows()
        .where(*filters)
        .order_by(*SORTING.order_by(sort))
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return [_row(found) for found in rows], total, total_amount, drawer_amount


def with_context(db: Session, expense_id: str) -> ExpenseRow | None:
    found = db.execute(_rows().where(Expense.id == expense_id)).first()
    return _row(found) if found else None


def many_with_context(db: Session, expense_ids: list[str]) -> list[ExpenseRow]:
    """In the order given, in one query."""
    rows = [_row(found) for found in db.execute(_rows().where(Expense.id.in_(expense_ids))).all()]
    by_id = {row.expense.id: row for row in rows}
    return [by_id[expense_id] for expense_id in expense_ids if expense_id in by_id]
