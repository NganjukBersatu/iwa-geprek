"""HTTP surface of the monthly summary."""
from fastapi import APIRouter, Depends, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import current_user
from app.core.clock import today
from app.core.database import get_db
from app.core.http import public_base_url
from app.core.period import MONTH_PATTERN, parse_month
from app.employee.attendance.summary import service
from app.employee.attendance.summary.mappers import summary_out
from app.employee.attendance.summary.schemas import AttendanceSummaryOut
from app.models.user import User

router = APIRouter(prefix="/attendance/summary", tags=["v2-attendance"])

SUMMARY = TypeAdapter(AttendanceSummaryOut)


@router.get("", response_model=AttendanceSummaryOut)
def monthly_summary(
    month: str | None = Query(None, pattern=MONTH_PATTERN, description="YYYY-MM; defaults to the current month"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Every signed-in employee may read their own record; no permission is needed."""
    current = today()
    month_start = parse_month(month) if month else current
    base_url = public_base_url()
    return cache.read(
        "app.attendance.summary",
        (*cache.viewer(user), month_start, base_url),
        lambda: summary_out(service.build_summary(db, user, month_start, current), base_url),
        SUMMARY,
        cache.LIST_SECONDS,
    )
