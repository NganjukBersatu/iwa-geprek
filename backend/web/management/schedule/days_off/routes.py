"""HTTP surface of days off; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_permission
from app.core.database import get_db
from app.core.date_range import Bound
from app.core.errors import DomainError
from app.employee.schedule.constants import PERMISSION_MANAGE, PERMISSION_VIEW
from app.models.user import User
from web.management.schedule.days_off import service
from web.management.schedule.days_off.domain import DayOffDraft
from web.management.schedule.days_off.mappers import day_off_out
from web.management.schedule.days_off.schemas import DayOffCreateIn, DayOffOut

router = APIRouter(prefix="/schedule/days-off", tags=["v2-schedule"])

DAYS_OFF = TypeAdapter(list[DayOffOut])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.get("", response_model=list[DayOffOut])
def list_days_off(
    start: Bound | None = Query(None, description="Defaults to Monday of this week"),
    end: Bound | None = Query(None, description="Defaults to six days after the start"),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    with _domain_errors():
        return cache.read(
            "web.schedule.days-off",
            (start, end, outlet_id),
            lambda: [day_off_out(item) for item in service.list_days_off(db, start, end, outlet_id)],
            DAYS_OFF,
            cache.LIST_SECONDS,
        )


@router.post("", response_model=DayOffOut, status_code=status.HTTP_201_CREATED)
def create_day_off(
    body: DayOffCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        return day_off_out(service.create(db, user.locked_outlet_id, DayOffDraft(**body.model_dump())))


@router.delete("/{day_off_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_day_off(
    day_off_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.delete(db, user.locked_outlet_id, day_off_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
