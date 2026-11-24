from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core import release_reads
from app.core.database import get_db
from app.core.release_reads import VERSION_MAX_LENGTH, VERSION_PATTERN, ReleaseReadIn, ReleaseReadOut
from app.models.release_read import Surface
from app.models.user import User
from web.management.access import web_user

router = APIRouter(tags=["web-management-releases"])


@router.get("/release-read", response_model=ReleaseReadOut)
def release_read(
    version: str = Query(pattern=VERSION_PATTERN, max_length=VERSION_MAX_LENGTH),
    db: Session = Depends(get_db),
    user: User = Depends(web_user),
):
    return release_reads.state_of(db, user.id, Surface.MANAGEMENT, version)


@router.patch("/release-read", response_model=ReleaseReadOut)
def mark_release_read(body: ReleaseReadIn, db: Session = Depends(get_db), user: User = Depends(web_user)):
    result = release_reads.mark_read(db, user.id, Surface.MANAGEMENT, body.version)
    db.commit()
    return result
