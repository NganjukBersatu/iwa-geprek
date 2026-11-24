"""HTTP surface of the activity timeline; every signed-in employee reads their own."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import current_user
from app.core.database import get_db
from app.employee.activity import service
from app.employee.activity.constants import DEFAULT_LIMIT, MAX_LIMIT
from app.employee.activity.domain import Group
from app.employee.activity.mappers import page_out
from app.employee.activity.schemas import ActivityPageOut
from app.models.user import User

router = APIRouter(prefix="/activity", tags=["v2-activity"])


@router.get("", response_model=ActivityPageOut)
def my_activity(
    before: datetime | None = Query(None, description="Only events older than this instant; the previous page's next_before"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    group: Group | None = Query(None, description="Only one kind of activity"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    return page_out(service.page(db, user.id, before, limit, group))
