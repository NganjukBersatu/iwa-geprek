"""Database reads for the attendance recap."""
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.business_days import valid_orders_in
from app.core.money import decimal_of
from app.models.attendance import Attendance
from app.models.order import Order
from app.models.outlet import Outlet
from app.models.overtime import Overtime
from app.models.schedule import Schedule
from app.models.user import User
from app.core.branches import branch_filter


def user_with_activity(db: Session, first: date, last: date, outlet_id: str | None) -> list[User]:
    """Anyone with a record, a schedule, or overtime in the range; someone only scheduled is exactly who may be absent."""
    recorded = select(Attendance.user_id).where(Attendance.date >= first, Attendance.date <= last, *branch_filter(Attendance.outlet_id, outlet_id))
    scheduled = select(Schedule.user_id).where(Schedule.date >= first, Schedule.date <= last, *branch_filter(Schedule.outlet_id, outlet_id))
    overtime = select(Overtime.user_id).where(Overtime.date >= first, Overtime.date <= last, *branch_filter(Overtime.outlet_id, outlet_id))
    found = db.scalars(select(User).where(User.id.in_(recorded) | User.id.in_(scheduled) | User.id.in_(overtime))).all()
    return sorted(found, key=lambda user: (user.name or user.username).lower())


def first_outlet_id(db: Session) -> str | None:
    return db.scalar(select(Outlet.id).order_by(Outlet.name).limit(1))


def revenue(db: Session, first: date, last: date, outlet_id: str | None) -> Decimal:
    return decimal_of(db.scalar(select(func.coalesce(func.sum(Order.total), 0)).where(*valid_orders_in(first, last, outlet_id))))
