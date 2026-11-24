"""Database reads and writes for a schedule an employee makes for themselves."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.outlet import Outlet
from app.models.role import Role
from app.models.schedule import Schedule
from app.models.shift_code import ShiftCode
from app.models.user import User


def lock_user(db: Session, user_id: str) -> None:
    """Holds the person's row until commit, so two requests at the same moment cannot both make a schedule."""
    db.execute(select(User.id).where(User.id == user_id).with_for_update())


def has_day_off_on(db: Session, user_id: str, day: date) -> bool:
    """A day off has no hours, so it is the one assignment still judged by its date."""
    return (
        db.scalar(
            select(Schedule.id)
            .join(ShiftCode, ShiftCode.id == Schedule.shift_code_id)
            .where(Schedule.user_id == user_id, Schedule.date == day, ShiftCode.is_day_off.is_(True))
            .limit(1)
        )
        is not None
    )


def outlets(db: Session) -> list[Outlet]:
    return list(db.scalars(select(Outlet).order_by(Outlet.name)).all())


def worker_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).where(Role.is_admin.is_(False)).order_by(Role.name)).all())


def working_codes(db: Session, outlet_id: str) -> list[ShiftCode]:
    """Codes of the branch that have a start clock and are not a day off."""
    return list(
        db.scalars(
            select(ShiftCode)
            .where(ShiftCode.outlet_id == outlet_id, ShiftCode.is_day_off.is_(False), ShiftCode.start_clock.is_not(None))
            .order_by(ShiftCode.sort_order, ShiftCode.code)
        ).all()
    )
