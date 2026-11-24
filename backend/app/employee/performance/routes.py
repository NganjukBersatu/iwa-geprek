"""HTTP surface of the performance charts; every signed-in employee reads their own."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import current_user
from app.core.clock import now
from app.core.database import get_db
from app.employee.performance import service
from app.employee.performance.domain import Range
from app.employee.performance.mappers import performance_out
from app.employee.performance.schemas import PerformanceOut
from app.models.user import User

router = APIRouter(prefix="/performance", tags=["v2-performance"])


@router.get("", response_model=PerformanceOut)
def my_performance(
    range: Range = Query(Range.CYCLE, description="cycle, previous, or all"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    return performance_out(service.build(db, user, range, now()))
