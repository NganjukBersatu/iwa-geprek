"""HTTP surface of overtime; every rule lives in the service."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import current_user, require_permission
from app.core.clock import today
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.period import MONTH_PATTERN, parse_month
from app.employee.overtime import ledger, service
from app.employee.overtime.constants import PERMISSION_SELF
from app.employee.overtime.mappers import overtime_out
from app.employee.overtime.schemas import OvertimeOut, UnplannedOvertimeIn
from app.models.user import User

router = APIRouter(prefix="/overtime", tags=["v2-overtime"])


def _as_http(error: DomainError) -> HTTPException:
    return HTTPException(status_code=error.status, detail=error.message)


@router.post("", response_model=OvertimeOut, status_code=status.HTTP_201_CREATED)
def record_unplanned_overtime(
    body: UnplannedOvertimeIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_SELF)),
):
    try:
        item = service.record_unplanned(db, user, body.started_at, body.ended_at, body.note)
    except DomainError as error:
        raise _as_http(error) from error
    return overtime_out(ledger.unplanned_entry(item))


@router.get("/mine", response_model=list[OvertimeOut])
def my_overtime(
    month: str | None = Query(None, pattern=MONTH_PATTERN, description="YYYY-MM; defaults to the current month"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    month_start = parse_month(month) if month else today()
    return [overtime_out(entry) for entry in service.history(db, user, month_start)]
