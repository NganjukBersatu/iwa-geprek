"""HTTP surface of notices; the app asks for them right after sign-in."""
from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import current_user
from app.core.clock import now
from app.core.database import get_db
from app.employee.notices import service
from app.employee.notices.constants import MAX_READ_IDS
from app.employee.notices.mappers import notice_out
from app.employee.notices.schemas import NoticeOut
from app.models.user import User

router = APIRouter(prefix="/notices", tags=["v2-notices"])


@router.get("", response_model=list[NoticeOut])
def my_notices(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [notice_out(notice) for notice in service.visible(db, user.id, now())]


@router.post("/read", status_code=status.HTTP_204_NO_CONTENT)
def read_notices(
    ids: list[UUID] = Body(..., embed=True, max_length=MAX_READ_IDS),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    service.mark_read(db, user.id, [str(item) for item in ids], now())
    db.commit()
