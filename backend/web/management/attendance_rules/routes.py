"""HTTP surface of the attendance rules; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import require_permission, writable_outlet_id
from app.core.database import get_db
from app.core.errors import DomainError
from app.employee.attendance.policy import BranchPolicy
from app.models.user import User
from web.management.attendance_rules import service
from web.management.attendance_rules.constants import PERMISSION_MANAGE
from web.management.attendance_rules.schemas import AttendanceRulesIn, AttendanceRulesOut

router = APIRouter(prefix="/attendance-rules", tags=["v2-attendance-rules"])

RULES = TypeAdapter(AttendanceRulesOut)


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _out(outlet_id: str, policy: BranchPolicy, is_default: bool) -> AttendanceRulesOut:
    return AttendanceRulesOut(
        outlet_id=outlet_id,
        late_tolerance_minutes=policy.late_tolerance_minutes,
        late_penalty_per_minute=policy.late_penalty_per_minute,
        auto_close_after_hours=policy.auto_close_after_hours,
        is_default=is_default,
    )


@router.get("", response_model=AttendanceRulesOut)
def read_rules(
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    def build() -> AttendanceRulesOut:
        with _domain_errors():
            policy, is_default = service.read(db, outlet_id)
        return _out(outlet_id, policy, is_default)

    return cache.read("web.attendance-rules", (outlet_id,), build, RULES, cache.REFERENCE_SECONDS)


@router.put("", response_model=AttendanceRulesOut)
def update_rules(
    body: AttendanceRulesIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        policy, is_default = service.update(db, outlet_id, body.model_dump(exclude_unset=True, exclude_none=True))
    return _out(outlet_id, policy, is_default)
