"""The answers for what FastAPI refuses by itself: a body that fails validation, and framework wording that was never meant for people."""
from http import HTTPStatus

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import error_page, messages
from app.core.errors import SERVER_ERROR, error_content

SERVICE_UNAVAILABLE = 503
WEB_RETRY_AFTER_SECONDS = "5"
VALIDATION_FAILED = "VALIDATION_FAILED"
INTERNAL_ERROR = "INTERNAL_ERROR"
UNPROCESSABLE = 422
# Statuses that never carry a body.
BODYLESS = frozenset({204, 304})
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
TOO_LARGE = 413
TOO_MANY_REQUESTS = 429
MAX_REPORTED_ERRORS = 20
PARSING_BODY_DETAIL = "There was an error parsing the body"

# The bare name of a status ("Not Found") and the parse failure are the framework's own words; any other detail is a sentence of ours.
_FRAMEWORK_DETAILS = frozenset({code.phrase for code in HTTPStatus} | {PARSING_BODY_DETAIL})
_BY_STATUS = {
    BAD_REQUEST: messages.HTTP_BAD_REQUEST,
    FORBIDDEN: messages.PERMISSION_DENIED,
    NOT_FOUND: messages.HTTP_NOT_FOUND,
    METHOD_NOT_ALLOWED: messages.HTTP_METHOD_NOT_ALLOWED,
    TOO_LARGE: messages.HTTP_TOO_LARGE,
    TOO_MANY_REQUESTS: messages.HTTP_TOO_MANY,
}

_NUMBER_PREFIXES = ("int_", "float_", "decimal_")
_DATE_PREFIXES = ("date", "time")
_CHOICE_TYPES = frozenset({"enum", "literal_error", "bool_parsing", "bool_type"})
_RANGE_TYPES = frozenset({"greater_than", "greater_than_equal", "less_than", "less_than_equal", "multiple_of"})
_UNREADABLE_TYPES = frozenset({"json_invalid", "json_type", "model_attributes_type", "dict_type", "list_type"})


def _sentence(item: dict) -> str:
    """One refused field as a sentence of ours; the library's own English wording and the value that was sent never leave."""
    kind = str(item.get("type", ""))
    context = item.get("ctx") or {}
    limit = context.get("max_length")
    if kind == "value_error":
        return str(context.get("error") or messages.VALIDATION_INVALID)
    if kind == "missing":
        return messages.VALIDATION_REQUIRED
    floor = context.get("min_length")
    if kind == "string_too_short" and isinstance(floor, int) and floor > 1:
        return messages.VALIDATION_TOO_SHORT_AT_LEAST.format(limit=floor)
    if kind == "string_too_short" and floor == 1:
        return messages.VALIDATION_REQUIRED
    if kind in {"string_too_short", "too_short"}:
        return messages.VALIDATION_TOO_SHORT
    if kind == "string_too_long":
        return messages.VALIDATION_TOO_LONG.format(limit=limit) if limit is not None else messages.VALIDATION_TOO_LONG_NO_LIMIT
    if kind == "too_long":
        return messages.VALIDATION_TOO_MANY.format(limit=limit) if limit is not None else messages.VALIDATION_INVALID
    if kind.startswith(_NUMBER_PREFIXES):
        return messages.VALIDATION_NOT_NUMBER
    if kind.startswith(_DATE_PREFIXES):
        return messages.VALIDATION_NOT_DATE
    if kind in _RANGE_TYPES:
        return messages.VALIDATION_OUT_OF_RANGE
    if kind in _CHOICE_TYPES or kind.startswith("uuid_"):
        return messages.VALIDATION_CHOICE
    if kind in _UNREADABLE_TYPES:
        return messages.VALIDATION_UNREADABLE
    return messages.VALIDATION_INVALID


async def validation_failed(_: Request, error: RequestValidationError) -> JSONResponse:
    """Keeps the status and the list shape clients already read, adds a stable code, and tells each refused field in Indonesian."""
    details = [
        {"loc": list(item.get("loc", ())), "type": str(item.get("type", "")), "msg": _sentence(item)}
        for item in list(error.errors())[:MAX_REPORTED_ERRORS]
    ]
    return JSONResponse(status_code=UNPROCESSABLE, content=error_content(UNPROCESSABLE, details, VALIDATION_FAILED))


async def framework_refusal(_: Request, error: StarletteHTTPException) -> Response:
    """Swaps the framework's English wording for a sentence of ours; a detail written by the application passes through untouched."""
    if error.status_code in BODYLESS:
        return Response(status_code=error.status_code, headers=error.headers)
    detail = error.detail
    if isinstance(detail, str) and detail in _FRAMEWORK_DETAILS:
        detail = _BY_STATUS.get(error.status_code, messages.HTTP_REFUSED)
    content = error_content(error.status_code, detail, getattr(error, "code", None), fields=getattr(error, "fields", None))
    return JSONResponse(status_code=error.status_code, content=content, headers=error.headers)


def web_unavailable(request: Request) -> Response:
    """The web server did not answer: a person opening a page gets a page with a way to try again, any other caller gets the coded answer."""
    headers = {"Retry-After": WEB_RETRY_AFTER_SECONDS}
    if "text/html" in request.headers.get("accept", ""):
        page = error_page.render(
            messages.WEB_UNAVAILABLE_TITLE,
            messages.WEB_UNAVAILABLE,
            messages.WEB_UNAVAILABLE_ACTION,
            messages.WEB_UNAVAILABLE_REFERENCE,
            getattr(request.state, "request_id", ""),
        )
        return HTMLResponse(page, status_code=SERVICE_UNAVAILABLE, headers=headers)
    return JSONResponse(status_code=SERVICE_UNAVAILABLE, content=error_content(SERVICE_UNAVAILABLE, messages.WEB_UNAVAILABLE), headers=headers)


async def unexpected_failure(request: Request, __: Exception) -> JSONResponse:
    """Whatever nothing else caught: the person gets a plain sentence and the request ID, never the exception."""
    request_id = getattr(request.state, "request_id", "")
    content = error_content(SERVER_ERROR, messages.SERVER_FAILED, INTERNAL_ERROR)
    content["request_id"] = request_id
    return JSONResponse(status_code=SERVER_ERROR, content=content, headers={"X-Request-ID": request_id} if request_id else None)
