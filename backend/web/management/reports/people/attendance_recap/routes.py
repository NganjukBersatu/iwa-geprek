"""HTTP surface of the attendance recap, rebuilt from the legacy /absensi/rekap route."""
from fastapi import APIRouter, Depends, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_gate
from app.core.database import get_db
from app.core.date_range import Bound
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.models.user import User
from web.management.reports.common import as_http
from web.management.reports.people.attendance_recap import service
from web.management.reports.people.attendance_recap.constants import RECAP_GATE
from web.management.reports.people.attendance_recap.mappers import attendance_recap_out
from web.management.reports.people.attendance_recap.schemas import AttendanceRecapOut

router = APIRouter(prefix="/reports/attendance", tags=["v2-reports"])

SHAPE = TypeAdapter(AttendanceRecapOut)


can_view_recap = require_gate(RECAP_GATE)


@router.get("", response_model=AttendanceRecapOut)
def attendance_recap(
    start: Bound | None = Query(None, description="Both empty means the month so far"),
    end: Bound | None = Query(None),
    sort: Sort = None,
    day_sort: Sort = None,
    overtime_sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(can_view_recap),
):
    """Present, late, leave, sick, and absent days, work and late minutes, overtime, and the late penalty per person."""
    try:
        return cache.read(
            "web.reports.attendance",
            (start, end, outlet_id, sort, day_sort, overtime_sort),
            lambda: attendance_recap_out(service.sorted_recap(service.attendance_recap(db, start, end, outlet_id), sort, day_sort, overtime_sort)),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
