import logging

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.auth import attempts
from app.core.database import get_db
from app.core.errors import BAD_REQUEST, CodedHTTPException, DomainError
from app.core.request_id import current_request_id
from app.csp_reports import messages, violations
from app.csp_reports.constants import ACCEPTED_MEDIA_TYPES, BUDGET, BUDGET_SUBJECT, MAX_BODY_BYTES

log = logging.getLogger(__name__)

PAYLOAD_TOO_LARGE = 413
UNSUPPORTED_MEDIA_TYPE = 415

router = APIRouter()


async def _body(request: Request) -> bytes:
    """Reads at most the limit, so a body that announces a small size and sends a large one is stopped as well."""
    announced = request.headers.get("content-length", "")
    if announced.isdigit() and int(announced) > MAX_BODY_BYTES:
        raise DomainError(messages.REPORT_TOO_LARGE, status=PAYLOAD_TOO_LARGE)
    received = bytearray()
    async for chunk in request.stream():
        received.extend(chunk)
        if len(received) > MAX_BODY_BYTES:
            raise DomainError(messages.REPORT_TOO_LARGE, status=PAYLOAD_TOO_LARGE)
    return bytes(received)


def _check_media_type(request: Request) -> None:
    media_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if media_type not in ACCEPTED_MEDIA_TYPES:
        raise DomainError(messages.REPORT_TYPE_NOT_ACCEPTED, status=UNSUPPORTED_MEDIA_TYPE)


@router.post("/csp-reports", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def receive_report(request: Request, db: Session = Depends(get_db)) -> Response:
    """Takes no sign-in because a browser sends it by itself; the size, the media type, and one shared budget are what protect it."""
    try:
        attempts.ensure_not_locked(db, BUDGET, BUDGET_SUBJECT)
        _check_media_type(request)
        content = await _body(request)
    except DomainError as error:
        raise attempts.refusal(error) from error
    try:
        found = violations.read(content)
    except ValueError as error:
        raise CodedHTTPException(BAD_REQUEST, messages.REPORT_UNREADABLE) from error
    for violation in found:
        attempts.record_failure(db, BUDGET, BUDGET_SUBJECT)
        log.warning(
            "csp violation directive=%s blocked=%s document=%s source=%s line=%s disposition=%s request_id=%s",
            violation.directive,
            violation.blocked,
            violation.document,
            violation.source,
            violation.line,
            violation.disposition,
            current_request_id(),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
