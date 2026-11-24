"""Serves stored files at the address the API hands out: open for the catalogue pictures, behind a sign-in and a right to the record for every other folder."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.auth import bearer_scheme, current_device, current_user
from app.core.database import get_db
from app.core.http import STATIC_PATH
from app.core.storage import access, files

router = APIRouter(include_in_schema=False)

# Only pictures that show no person and no money record; every other folder needs an access check first (15.3).
PUBLIC_FOLDERS = frozenset({"menu", "bahan", "metode-bayar", "promosi"})
# A stored file is never overwritten (a new upload gets a new name), so a copy never goes stale.
PUBLIC_CACHE_CONTROL = "public, max-age=31536000, immutable"
# Private files stay out of shared caches, and a withdrawn right reaches a browser that already holds a copy within the hour.
PRIVATE_CACHE_CONTROL = "private, max-age=3600"


def _is_well_formed(path: str) -> bool:
    parts = path.split("/")
    return len(parts) >= 2 and all(part not in ("", ".", "..") for part in parts)


def _is_public(path: str) -> bool:
    return path.split("/")[0] in PUBLIC_FOLDERS


def _may_read_private(request: Request, credentials: HTTPAuthorizationCredentials | None, db: Session, path: str) -> bool:
    """A tablet sends its device token and a person sends a session token; a missing or unknown one answers 401 like every other route."""
    if credentials is not None:
        try:
            return access.device_may_read(db, current_device(credentials, db), path)
        except HTTPException:
            pass
    return access.user_may_read(db, current_user(request, credentials, db), path)


@router.get(f"/{STATIC_PATH}/{{path:path}}")
def stored_file(
    path: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Response:
    if not _is_well_formed(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    public = _is_public(path)
    # A refusal is "not found", so nobody learns from the answer which files exist.
    if not public and not _may_read_private(request, credentials, db, path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    found = files.read(db, path)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    content, content_type = found
    return Response(content=content, media_type=content_type, headers={"Cache-Control": PUBLIC_CACHE_CONTROL if public else PRIVATE_CACHE_CONTROL})
