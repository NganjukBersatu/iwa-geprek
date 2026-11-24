"""HTTP surface of the schedule screens."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import current_user, readable_outlet_id, require_permission
from app.core.clock import today
from app.core.database import get_db
from app.core.period import MONTH_PATTERN, parse_month
from app.employee.schedule.board import service
from app.employee.schedule.board.constants import PERMISSION_VIEW
from app.employee.schedule.board.mappers import assignment_out, month_board_out
from app.employee.schedule.board.schemas import BoardAssignmentOut, MonthBoardOut
from app.models.user import User

router = APIRouter(prefix="/schedule", tags=["v2-schedule"])

BOARD = TypeAdapter(MonthBoardOut)
ASSIGNMENTS = TypeAdapter(list[BoardAssignmentOut])


@router.get("/month", response_model=MonthBoardOut)
def month_board(
    month: str | None = Query(None, pattern=MONTH_PATTERN, description="YYYY-MM; defaults to the current month"),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
    outlet_id: str | None = Depends(readable_outlet_id),
):
    month_start = parse_month(month) if month else today()
    return cache.read(
        "app.schedule.month",
        (outlet_id, month_start),
        lambda: month_board_out(service.month_board(db, outlet_id, month_start)),
        BOARD,
        cache.LIST_SECONDS,
    )


@router.get("/mine", response_model=list[BoardAssignmentOut])
def my_assignments(
    day: date | None = Query(None, alias="date", description="Defaults to today"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    chosen = day or today()
    return cache.read(
        "app.schedule.mine", (user.id, chosen), lambda: [assignment_out(item) for item in service.my_assignments(db, user.id, chosen)], ASSIGNMENTS, cache.LIST_SECONDS
    )
