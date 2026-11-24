"""Closing periods of the tablet's branch, set on the web; the rules live in app.core.branch_periods."""
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import branch_periods
from app.core.auth import current_user
from app.core.clock import today
from app.core.database import get_db
from app.models.device import Device
from app.models.outlet import Outlet
from app.models.user import User
from app.operational.device import tablet

router = APIRouter(prefix="/periods", tags=["v2-operational-periods"])


class TabletPeriodOut(BaseModel):
    start: date
    end: date
    running: bool


# Not cached: a handful of rows read when a list opens, and a period changed on the web must show on the next open.
@router.get("", response_model=list[TabletPeriodOut])
def list_periods(device: Device = Depends(tablet), db: Session = Depends(get_db), _user: User = Depends(current_user)):
    """Periods already started at the tablet's branch, the running one first."""
    outlet = db.scalar(select(Outlet).where(Outlet.id == device.outlet_id))
    if outlet is None:
        return []
    day = today()
    return [TabletPeriodOut(start=period.start, end=period.end, running=period.start <= day <= period.end) for period in branch_periods.listing(db, [outlet], day)[outlet.id]]
