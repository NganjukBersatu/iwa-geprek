"""What has been handed over to the owner per branch and business day, and the state of a day before its money is changed."""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field
from sqlalchemy import func, select, tuple_
from sqlalchemy.orm import Session

from app.core.bulk import MAX_ROWS
from app.core.business_days import first_unfinished_day
from app.core.finance.session_control import active_of
from app.core.money import ZERO, decimal_of
from app.models.deposit import Deposit, DepositDay
from app.models.expense import Expense

MAX_DAYS_ASKED = 100


class DayKey(BaseModel):
    outlet_id: str
    day: date


class DayStatesIn(BaseModel):
    """Days named directly, the days of the expenses about to change, and the reader's running session, where a new expense lands."""

    days: list[DayKey] = Field(default_factory=list, max_length=MAX_DAYS_ASKED)
    expense_ids: list[str] = Field(default_factory=list, max_length=MAX_ROWS)
    running_session: bool = False


class DayStateOut(BaseModel):
    outlet_id: str
    day: date
    # Zero when nothing of that day has been handed over yet.
    deposited: Decimal
    # A session of that day is still running, so its money can still change.
    unfinished: bool


def paid_by_outlet(db: Session, outlet_ids: list[str], start: date, end: date) -> dict[str, dict[date, Decimal]]:
    """What each branch has handed over per income day, in one grouped query for all the branches asked for."""
    paid: dict[str, dict[date, Decimal]] = {outlet_id: {} for outlet_id in outlet_ids}
    rows = db.execute(
        select(Deposit.outlet_id, DepositDay.day, func.sum(DepositDay.amount))
        .join(Deposit, Deposit.id == DepositDay.deposit_id)
        .where(Deposit.outlet_id.in_(outlet_ids), DepositDay.day >= start, DepositDay.day <= end)
        .group_by(Deposit.outlet_id, DepositDay.day)
    ).all()
    for outlet_id, day, total in rows:
        paid[outlet_id][day] = decimal_of(total)
    return paid


def paid_by_day(db: Session, outlet_id: str, start: date, end: date) -> dict[date, Decimal]:
    return paid_by_outlet(db, [outlet_id], start, end)[outlet_id]


def day_states(db: Session, asked: DayStatesIn, outlet_id: str | None, user_id: str) -> list[DayStateOut]:
    """In the order asked, in at most three queries however many days; each day once, and only the branch the reader may see when it is bound to one."""
    keys = [(key.outlet_id, key.day) for key in asked.days]
    if asked.expense_ids:
        keys += db.execute(select(Expense.outlet_id, Expense.business_day).where(Expense.id.in_(asked.expense_ids)).distinct()).tuples().all()
    if asked.running_session:
        running = active_of(db, user_id)
        if running is not None:
            keys.append((running.outlet_id, running.business_day))
    wanted = list(dict.fromkeys((branch, day) for branch, day in keys if outlet_id is None or branch == outlet_id))
    if not wanted:
        return []
    paid = {
        (outlet_id, day): decimal_of(total)
        for outlet_id, day, total in db.execute(
            select(Deposit.outlet_id, DepositDay.day, func.sum(DepositDay.amount))
            .join(Deposit, Deposit.id == DepositDay.deposit_id)
            .where(tuple_(Deposit.outlet_id, DepositDay.day).in_(wanted))
            .group_by(Deposit.outlet_id, DepositDay.day)
        ).all()
    }
    unfinished = first_unfinished_day(db, list({outlet_id for outlet_id, _ in wanted}))
    return [
        DayStateOut(outlet_id=outlet_id, day=day, deposited=paid.get((outlet_id, day), ZERO), unfinished=day >= unfinished[outlet_id])
        for outlet_id, day in wanted
    ]
