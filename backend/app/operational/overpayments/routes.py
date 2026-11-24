"""Overpayments of the tablet's branch; the report lives in app.core.finance.overpayment_report."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_permission
from app.core.database import get_db
from app.core.date_range import Day
from app.core.finance import overpayment_report
from app.core.finance.overpayment_report import OverpaymentsOut
from app.core.sorting import Sort
from app.models.device import Device
from app.models.user import User
from app.operational.device import tablet

router = APIRouter(prefix="/overpayments", tags=["v2-operational-overpayments"])

PERMISSION_VIEW = "kelebihan.lihat"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
RANGE_REVERSED = "Tanggal awal harus sebelum tanggal akhir."


@router.get("", response_model=OverpaymentsOut)
def overpayments(
    start: Day = Query(...),
    end: Day = Query(...),
    user_id: str | None = Query(None, max_length=64, description="Only overpayments recorded by this user member"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(PERMISSION_VIEW)),
):
    if start > end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=RANGE_REVERSED)
    return overpayment_report.report(db, start, end, device.outlet_id, user_id, None, sort, page, size)
