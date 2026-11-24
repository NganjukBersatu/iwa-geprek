from pydantic import BaseModel, Field

from app.employee.devices.constants import MAX_CODE_LENGTH, MAX_TOKEN_LENGTH, MIN_TOKEN_LENGTH


class PairIn(BaseModel):
    code: str = Field(min_length=1, max_length=MAX_CODE_LENGTH)
    android_id: str | None = Field(None, max_length=64)
    serial: str | None = Field(None, max_length=80)
    brand: str | None = Field(None, max_length=60)
    model: str | None = Field(None, max_length=80)


class PairedDeviceOut(BaseModel):
    id: str
    outlet_id: str
    name: str
    section: str
    # Shown once; the server keeps only its hash.
    token: str


class LinkIn(BaseModel):
    token: str = Field(min_length=MIN_TOKEN_LENGTH, max_length=MAX_TOKEN_LENGTH)


class LinkedDeviceOut(BaseModel):
    device_name: str
    section: str


class QrOut(BaseModel):
    id: str
    token: str
    valid_seconds: int


class QrStatusOut(BaseModel):
    status: str
    user_name: str | None = None
    access_token: str | None = None
