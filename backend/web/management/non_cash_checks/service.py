"""Compares the non-cash money the system recorded with the bank figure an admin typed, day by day.

A day without a bank figure is not wrong, it is just not checked yet. The difference is never stored: the recorded
figure can still move when an order is voided later, so it is worked out again on every read.
"""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.branches import outlet_name, outlets_in_scope
from app.core.clock import today
from app.core.errors import DomainError
from app.core.finance.payment_methods import open_non_cash_labels
from app.core.money import ZERO, decimal_of
from web.management.non_cash_checks import messages, repository
from web.management.non_cash_checks.constants import STATUS_BALANCED, STATUS_MISMATCH, STATUS_PENDING
from web.management.non_cash_checks.model import NonCashCheck
from web.management.non_cash_checks.schemas import NonCashCheckRowOut, NonCashChecksOut, NonCashCheckSummaryOut
from web.management.reports.common import month_to_date

ALL = "all"


def _status(difference: Decimal | None) -> str:
    if difference is None:
        return STATUS_PENDING
    return STATUS_BALANCED if difference == 0 else STATUS_MISMATCH


def _row(day: date, outlet_id: str, branch_name: str, recorded: Decimal, check: NonCashCheck | None) -> NonCashCheckRowOut:
    bank = None if check is None else decimal_of(check.bank_amount)
    difference = None if bank is None else bank - recorded
    return NonCashCheckRowOut(outlet_id=outlet_id, outlet_name=branch_name, date=day, recorded=recorded, bank_amount=bank, difference=difference, status=_status(difference))


def checks(db: Session, start: date | None, end: date | None, status: str, outlet_id: str | None) -> NonCashChecksOut:
    """The summary always covers the whole range, so its figures do not move when the status filter changes. With no branch every active branch gets its own row for each day."""
    start, end = month_to_date(start, end)
    branches = outlets_in_scope(db, outlet_id)
    branch_ids = [branch.id for branch in branches]
    recorded, saved = repository.recorded_by_outlet(db, branch_ids, start, end), repository.checks_by_outlet(db, branch_ids, start, end)

    rows = []
    day = start
    while day <= end:
        for branch in branches:
            rows.append(_row(day, branch.id, branch.name, recorded[branch.id].get(day, ZERO), saved[branch.id].get(day)))
        day += timedelta(days=1)

    summary = NonCashCheckSummaryOut(
        balanced=sum(row.status == STATUS_BALANCED for row in rows),
        mismatch=sum(row.status == STATUS_MISMATCH for row in rows),
        pending=sum(row.status == STATUS_PENDING for row in rows),
        total_difference=sum((row.difference for row in rows if row.difference is not None), ZERO),
    )
    shown = rows if status == ALL else [row for row in rows if row.status == status]
    return NonCashChecksOut(outlet_id=outlet_id, start=start, end=end, methods=open_non_cash_labels(db, branch_ids), rows=shown, summary=summary)


def save(db: Session, day: date, bank_amount: Decimal, outlet_id: str, user_id: str) -> NonCashCheckRowOut:
    if day > today():
        raise DomainError(messages.FUTURE_DATE)
    check = repository.find(db, outlet_id, day)
    if check is None:
        check = NonCashCheck(outlet_id=outlet_id, date=day, bank_amount=bank_amount)
        db.add(check)
    else:
        check.bank_amount = bank_amount
    check.entered_by = user_id
    db.commit()
    return _row(day, outlet_id, outlet_name(db, outlet_id) or "", repository.recorded_by_outlet(db, [outlet_id], day, day)[outlet_id].get(day, ZERO), check)


def clear(db: Session, day: date, outlet_id: str) -> None:
    check = repository.find(db, outlet_id, day)
    if check is not None:
        db.delete(check)
        db.commit()
