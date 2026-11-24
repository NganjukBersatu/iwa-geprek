"""Laporan kegagalan izin dari gerbang izin PWA; hanya ditulis ke log, tidak ke database."""
import logging
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core import messages
from app.core.auth import current_user
from app.employee.client_events import throttle
from app.employee.client_events.constants import MAX_AGENT_LENGTH, MAX_HEADER_LENGTH
from app.employee.client_events.schemas import PermissionFailureIn
from app.models.user import User

log = logging.getLogger("cafe.client")

router = APIRouter(prefix="/client-events", tags=["v2-client-events"])


@router.post("/permission-failures", status_code=status.HTTP_204_NO_CONTENT)
def permission_failure(body: PermissionFailureIn, request: Request, user: User = Depends(current_user)) -> None:
    wait = throttle.retry_after_seconds(str(user.id), monotonic())
    if wait is not None:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, messages.HTTP_TOO_MANY, headers={"Retry-After": str(wait)})
    log.warning(
        "permission gate failed: user=%s ref=%s kind=%s reason=%s elapsed_millis=%d client=%r version=%r agent=%r",
        user.id,
        body.reference,
        body.kind.value,
        body.reason.value,
        body.elapsed_millis,
        request.headers.get("x-app-client", "")[:MAX_HEADER_LENGTH],
        request.headers.get("x-app-version", "")[:MAX_HEADER_LENGTH],
        request.headers.get("user-agent", "")[:MAX_AGENT_LENGTH],
    )
