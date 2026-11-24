from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.employee.client_events.constants import MAX_ELAPSED_MILLIS, REFERENCE_PATTERN


class PermissionKind(StrEnum):
    LOCATION = "location"
    CAMERA = "camera"
    GPS = "gps"


class PermissionReason(StrEnum):
    DENIED = "denied"
    TIMEOUT = "timeout"
    SERVICE_OFF = "service_off"
    UNANSWERED = "unanswered"
    MISSING = "missing"
    BUSY = "busy"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class PermissionFailureIn(BaseModel):
    """Hanya nilai dari daftar tetap yang diterima, sehingga isi log tidak bisa diisi teks bebas."""

    model_config = ConfigDict(extra="forbid")

    kind: PermissionKind
    reason: PermissionReason
    elapsed_millis: int = Field(ge=0, le=MAX_ELAPSED_MILLIS)
    reference: str = Field(pattern=REFERENCE_PATTERN)
