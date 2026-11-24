"""HTTP surface of the self-made schedule; the clock-in after it is the ordinary one."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_permission
from app.core.clock import now
from app.core.database import get_db
from app.core.errors import DomainError
from app.employee.attendance import mappers
from app.employee.attendance.constants import MAX_ID_LENGTH, PERMISSION_SELF_ATTENDANCE
from app.employee.attendance.schemas import ScheduleSummary
from app.employee.attendance.self_schedule import service
from app.employee.attendance.self_schedule.mappers import options_out
from app.employee.attendance.self_schedule.schemas import SelfScheduleIn, SelfScheduleOptionsOut
from app.models.user import User

router = APIRouter(prefix="/attendance/self-schedule", tags=["v2-attendance"])


@router.get("/options", response_model=SelfScheduleOptionsOut)
def self_schedule_options(
    outlet_id: str | None = Query(None, max_length=MAX_ID_LENGTH, description="The branch whose shift codes are suggested"),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_SELF_ATTENDANCE)),
):
    return options_out(service.options(db, user, outlet_id, now()))


@router.post("", response_model=ScheduleSummary, status_code=status.HTTP_201_CREATED)
def create_self_schedule(
    body: SelfScheduleIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_SELF_ATTENDANCE)),
):
    try:
        schedule = service.create(db, user, body.outlet_id, body.role_id, body.shift_code_id, body.reason, now())
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    db.commit()
    db.refresh(schedule)
    return mappers.schedule_summary(schedule)
