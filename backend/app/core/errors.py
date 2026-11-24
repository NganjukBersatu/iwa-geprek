"""The one place an error answer is written: a stable code, the sentence for the person, and the request ID.

`detail` keeps carrying the sentence because the apps already read it; `code` is what a client should decide on, and never changes meaning.
"""
from fastapi import HTTPException

from app.core.request_id import current_request_id

BAD_REQUEST = 400
SERVER_ERROR = 500
SERVICE_UNAVAILABLE = 503

# The code a status gets when the rule that raised it did not name a more exact one.
_CODE_BY_STATUS = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    412: "PRECONDITION_FAILED",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_FAILED",
    426: "CLIENT_OUTDATED",
    428: "PRECONDITION_REQUIRED",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_ERROR",
    503: "UNAVAILABLE",
}


def code_for(status: int, code: str | None = None) -> str:
    return code or _CODE_BY_STATUS.get(status, f"HTTP_{status}")


def error_content(status: int, detail: object, code: str | None = None, fields: dict[str, str] | None = None) -> dict:
    """The body of every error answer; `fields` names the request fields a rule refused, so a screen can show each sentence under its own box."""
    content = {"code": code_for(status, code), "detail": detail, "request_id": current_request_id()}
    if fields:
        content["fields"] = fields
    return content


class DomainError(Exception):
    """Raised by v2 services when a business rule rejects a request; `code` names the rule when the status alone is not exact enough."""

    def __init__(self, message: str, status: int = BAD_REQUEST, code: str | None = None, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        # The name of the request field the rule is about, as the screen sends it; empty when the rule concerns the request as a whole.
        self.field = field

    @property
    def fields(self) -> dict[str, str]:
        return {self.field: self.message} if self.field else {}


class CodedHTTPException(HTTPException):
    """An HTTP refusal that names its rule, for the places that must raise through the framework instead of a service."""

    def __init__(self, status_code: int, detail: str, code: str | None = None, headers: dict[str, str] | None = None, fields: dict[str, str] | None = None) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code
        self.fields = fields or {}


def refusal(error: DomainError) -> CodedHTTPException:
    """A rule that refused a request, as the HTTP answer: its status, its sentence, its code, and the field it is about."""
    return CodedHTTPException(error.status, error.message, error.code, fields=error.fields)
