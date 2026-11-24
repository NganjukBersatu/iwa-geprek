"""HTTP surface of the day plan; every signed-in employee reads their own."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import current_user
from app.core.clock import now
from app.core.database import get_db
from app.employee.day_plan import service
from app.employee.day_plan.mappers import day_plan_out
from app.employee.day_plan.schemas import DayPlanOut
from app.models.user import User

router = APIRouter(prefix="/day-plan", tags=["v2-day-plan"])


@router.get("", response_model=DayPlanOut)
def my_day_plan(db: Session = Depends(get_db), user: User = Depends(current_user)):
    instant = now()
    return day_plan_out(service.build(db, user, instant), instant)
