"""The attendance rules a branch has chosen; the employee side reads them through BranchPolicy."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import branch_settings
from app.core.errors import DomainError
from app.employee.attendance.policy import BranchPolicy
from app.models.cafe_settings import CafeSettings
from app.models.outlet import Outlet
from web.management.attendance_rules import messages

NOT_FOUND = 404
CHANGEABLE = ("late_tolerance_minutes", "late_penalty_per_minute", "auto_close_after_hours")


def read(db: Session, outlet_id: str) -> tuple[BranchPolicy, bool]:
    """The rules in force, and whether they are only the defaults because the branch has no settings row."""
    _ensure_outlet(db, outlet_id)
    return BranchPolicy.load(db, outlet_id), db.get(CafeSettings, outlet_id) is None


def update(db: Session, outlet_id: str, values: dict[str, int]) -> tuple[BranchPolicy, bool]:
    _ensure_outlet(db, outlet_id)
    row = branch_settings.ensure(db, outlet_id)
    for field in CHANGEABLE:
        if field in values:
            setattr(row, field, values[field])
    db.commit()
    return BranchPolicy.load(db, outlet_id), False


def _ensure_outlet(db: Session, outlet_id: str) -> None:
    if db.scalar(select(Outlet.id).where(Outlet.id == outlet_id)) is None:
        raise DomainError(messages.BRANCH_UNKNOWN, status=NOT_FOUND)
