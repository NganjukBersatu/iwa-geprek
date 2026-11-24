"""Database reads for the people a schedule arranger can place."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import protection
from app.models.user import User


def active_user(db: Session, outlet_id: str | None) -> list[User]:
    statement = select(User).where(User.is_active.is_(True), protection.schedulable())
    if outlet_id:
        statement = statement.where(User.outlet_id == outlet_id)
    return list(db.scalars(statement.order_by(User.username)).all())
