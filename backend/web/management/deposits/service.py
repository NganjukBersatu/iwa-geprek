"""Cash that goes to the owner: which income days are settled, how much is still held, and the deposits that settled them."""
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core import clock, uploads
from app.core.branches import branch_ids_in_scope
from app.core.errors import DomainError
from app.core.finance import deposited
from app.core.money import ZERO
from app.core.uploads import UploadedFile, UploadRule
from app.models.deposit import Deposit, DepositDay
from app.models.user import User
from web.management.deposits import messages, repository
from web.management.deposits.constants import MAX_DAYS, NOT_FOUND, OPEN, PARTIAL, PHOTO_FOLDER, SETTLED
from web.management.deposits.domain import allocate, status_of
from web.management.reports.common import month_to_date
from web.management.reports.sales.daily_overview import service as daily_overview


@dataclass(frozen=True)
class DayState:
    day: date
    due: Decimal
    paid: Decimal
    left: Decimal
    status: str


@dataclass(frozen=True)
class Summary:
    held: Decimal
    oldest_open_day: date | None
    paid_total: Decimal
    deposit_count: int
    last_deposit_date: date | None
    without_photo: int


@dataclass(frozen=True)
class DepositDraft:
    deposit_date: date
    amount: Decimal
    note: str | None
    days: list[date]


def plain(day: date) -> date:
    """A report bound may carry a clock time; a deposit only ever deals in calendar days."""
    return date(day.year, day.month, day.day)


def _tidy(text: str | None) -> str | None:
    cleaned = (text or "").strip()
    return cleaned or None


def due_by_outlet(db: Session, outlet_ids: list[str], start: date, end: date) -> dict[str, dict[date, Decimal]]:
    """What each day owes the owner is its cash profit; a day that spent as much cash as it took, or more, owes nothing. Two queries for all the branches."""
    profit = daily_overview.cash_profit_by_outlet(db, start, end, outlet_ids)
    return {outlet_id: {plain(day): max(value, ZERO) for day, value in days.items()} for outlet_id, days in profit.items()}


def due_by_day(db: Session, outlet_id: str, start: date, end: date) -> dict[date, Decimal]:
    return due_by_outlet(db, [outlet_id], start, end)[outlet_id]


def _states_of(due: dict[date, Decimal], paid: dict[date, Decimal]) -> list[DayState]:
    items = []
    for day in sorted(set(due) | set(paid)):
        owed, given = due.get(day, ZERO), paid.get(day, ZERO)
        if owed <= 0 and given <= 0:
            continue
        items.append(DayState(day, owed, given, max(owed - given, ZERO), status_of(owed, given)))
    return items


def _merged(states: list[DayState]) -> list[DayState]:
    """Several branches on one day: what is owed, paid, and still held add up; a branch that paid more than it owed does not cover another."""
    by_day: dict[date, list[DayState]] = {}
    for state in states:
        by_day.setdefault(state.day, []).append(state)
    merged = []
    for day in sorted(by_day):
        parts = by_day[day]
        owed = sum((part.due for part in parts), ZERO)
        given = sum((part.paid for part in parts), ZERO)
        left = sum((part.left for part in parts), ZERO)
        status = status_of(owed, given) if len(parts) == 1 else (OPEN if given <= 0 else (SETTLED if left <= 0 else PARTIAL))
        merged.append(DayState(day, owed, given, left, status))
    return merged


def days_view(db: Session, outlet_id: str | None, start: date | None, end: date | None) -> tuple[date, date, list[DayState], Summary]:
    """One branch's days, or, with no branch, every active branch's added up day by day."""
    first, last = month_to_date(start, end)
    first, last = plain(first), plain(last)
    branch_ids = branch_ids_in_scope(db, outlet_id)
    due, paid = due_by_outlet(db, branch_ids, first, last), deposited.paid_by_outlet(db, branch_ids, first, last)
    items = _merged([state for branch_id in branch_ids for state in _states_of(due[branch_id], paid[branch_id])])
    deposits = [deposit for deposit, _ in repository.touching(db, outlet_id, first, last)]
    open_days = [item.day for item in items if item.left > 0]
    summary = Summary(
        held=sum((item.left for item in items), ZERO),
        oldest_open_day=open_days[0] if open_days else None,
        paid_total=sum((item.paid for item in items), ZERO),
        deposit_count=len(deposits),
        last_deposit_date=max((deposit.deposit_date for deposit in deposits), default=None),
        without_photo=sum(1 for deposit in deposits if not deposit.photo_path),
    )
    return first, last, items, summary


def create(db: Session, user: User, outlet_id: str, draft: DepositDraft) -> Deposit:
    if draft.deposit_date > clock.today():
        raise DomainError(messages.FUTURE_DATE)
    days = sorted({plain(day) for day in draft.days})
    if not days:
        raise DomainError(messages.NOTHING_TO_DEPOSIT)
    if (days[-1] - days[0]).days >= MAX_DAYS:
        raise DomainError(messages.TOO_MANY_DAYS)
    due = due_by_day(db, outlet_id, days[0], days[-1])
    paid = deposited.paid_by_day(db, outlet_id, days[0], days[-1])
    open_days = []
    for day in days:
        left = due.get(day, ZERO) - paid.get(day, ZERO)
        if left <= 0:
            raise DomainError(messages.DAY_NOT_OPEN.format(day=f"{day:%d/%m/%Y}"))
        open_days.append((day, left))
    shares = allocate(draft.amount, open_days)
    last = max(shares)
    if draft.deposit_date < last:
        raise DomainError(messages.BEFORE_INCOME.format(day=f"{last:%d/%m/%Y}"))
    deposit = Deposit(
        outlet_id=outlet_id,
        deposit_date=draft.deposit_date,
        amount=draft.amount,
        note=_tidy(draft.note),
        user_id=user.id,
        days=[DepositDay(day=day, amount=amount) for day, amount in shares.items()],
    )
    db.add(deposit)
    db.commit()
    return deposit


def _own(db: Session, outlet_id: str, deposit_id: str) -> Deposit:
    deposit = repository.find(db, outlet_id, deposit_id)
    if deposit is None:
        raise DomainError(messages.DEPOSIT_NOT_FOUND, status=NOT_FOUND)
    return deposit


def set_note(db: Session, outlet_id: str, deposit_id: str, note: str | None) -> Deposit:
    deposit = _own(db, outlet_id, deposit_id)
    deposit.note = _tidy(note)
    db.commit()
    return deposit


def delete(db: Session, outlet_id: str, deposit_id: str) -> None:
    """Cancelling takes the deposit and its shares away, so every day it settled is held again."""
    deposit = _own(db, outlet_id, deposit_id)
    photo = deposit.photo_path
    db.delete(deposit)
    db.commit()
    uploads.discard(db, photo)


def set_photo(db: Session, outlet_id: str, deposit_id: str, image: UploadedFile, rule: UploadRule) -> Deposit:
    deposit = _own(db, outlet_id, deposit_id)
    path = f"{PHOTO_FOLDER}/{deposit.id}/{uuid.uuid4()}{image.extension}"
    uploads.store(db, path, image, rule)
    previous = deposit.photo_path
    deposit.photo_path = path
    db.commit()
    uploads.discard(db, previous)
    return deposit
