"""Reads and plain writes of deposits; no rule lives here."""
from datetime import date

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.models.deposit import Deposit, DepositDay
from app.models.user import User


def touching(db: Session, outlet_id: str | None, start: date, end: date) -> list[tuple[Deposit, str | None]]:
    """Deposits that settled at least one day of the range, newest first; every branch's when no branch is given."""
    inside = exists().where(DepositDay.deposit_id == Deposit.id, DepositDay.day >= start, DepositDay.day <= end)
    query = select(Deposit, func.coalesce(User.name, User.username)).outerjoin(User, User.id == Deposit.user_id).where(inside)
    if outlet_id is not None:
        query = query.where(Deposit.outlet_id == outlet_id)
    rows = db.execute(query.order_by(Deposit.deposit_date.desc(), Deposit.created_at.desc(), Deposit.id)).all()
    return [(deposit, name) for deposit, name in rows]


def find(db: Session, outlet_id: str, deposit_id: str) -> Deposit | None:
    deposit = db.get(Deposit, deposit_id)
    return deposit if deposit is not None and deposit.outlet_id == outlet_id else None


def with_user(db: Session, deposit_id: str) -> tuple[Deposit, str | None] | None:
    row = db.execute(
        select(Deposit, func.coalesce(User.name, User.username)).outerjoin(User, User.id == Deposit.user_id).where(Deposit.id == deposit_id)
    ).first()
    return (row[0], row[1]) if row else None
