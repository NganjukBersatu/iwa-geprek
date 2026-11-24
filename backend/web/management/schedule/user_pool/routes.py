"""The active people a schedule arranger can place, kept apart from /user so arranging needs no karyawan.kelola."""
from fastapi import APIRouter, Depends
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_permission
from app.core.database import get_db
from app.employee.schedule.constants import PERMISSION_MANAGE
from app.models.user import User
from web.management.schedule.user_pool import repository
from web.management.schedule.user_pool.mappers import pool_user_out
from web.management.schedule.user_pool.schemas import PoolUserOut

router = APIRouter(prefix="/schedule/users", tags=["v2-schedule"])

POOL = TypeAdapter(list[PoolUserOut])


@router.get("", response_model=list[PoolUserOut])
def user_pool(
    db: Session = Depends(get_db),
    outlet_id: str | None = Depends(readable_outlet_id),
    _user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    """A branch-bound arranger only sees people placed at their own branch; others see the branch they filter by, or all."""
    return cache.read(
        "web.schedule.user", (outlet_id,), lambda: [pool_user_out(person) for person in repository.active_user(db, outlet_id)], POOL, cache.REFERENCE_SECONDS
    )
