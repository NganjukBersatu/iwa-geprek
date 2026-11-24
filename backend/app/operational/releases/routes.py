from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core import release_reads
from app.core.auth import current_user
from app.core.database import get_db
from app.core.release_reads import VERSION_MAX_LENGTH, VERSION_PATTERN, ReleaseReadIn, ReleaseReadOut
from app.models.device import Device
from app.models.release_read import Surface
from app.models.user import User
from app.operational.device import tablet

router = APIRouter(tags=["v2-operational-releases"])


@router.get("/release-read", response_model=ReleaseReadOut)
def release_read(
    version: str = Query(pattern=VERSION_PATTERN, max_length=VERSION_MAX_LENGTH),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    _device: Device = Depends(tablet),
):
    return release_reads.state_of(db, user.id, Surface.OPERATIONAL, version)


@router.patch("/release-read", response_model=ReleaseReadOut)
def mark_release_read(
    body: ReleaseReadIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    _device: Device = Depends(tablet),
):
    result = release_reads.mark_read(db, user.id, Surface.OPERATIONAL, body.version)
    db.commit()
    return result
