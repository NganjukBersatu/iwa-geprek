from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.devices.device_stations import MAX_STATIONS
from app.models.station import StationKind
from web.management.devices.constants import MAX_NAME_LENGTH

DeviceMode = Literal["cashier", "station"]


class DeviceCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    # Dengan mode: semua stasiun yang dicentang, dan server menurunkan yang dipegang serta yang dicetak dari tablet ini.
    # Tanpa mode (klien lama): stasiun yang dipegang tablet ini.
    station_ids: list[str] = Field(default_factory=list, max_length=MAX_STATIONS)
    # Klien lama saja: stasiun tanpa tablet yang struknya dikirim dari tablet ini; diabaikan bila mode dikirim.
    print_station_ids: list[str] = Field(default_factory=list, max_length=MAX_STATIONS)
    mode: DeviceMode | None = None


class DeviceUpdateIn(BaseModel):
    """A field left out stays as it was."""

    name: str | None = Field(None, min_length=1, max_length=MAX_NAME_LENGTH)
    station_ids: list[str] | None = Field(None, max_length=MAX_STATIONS)
    print_station_ids: list[str] | None = Field(None, max_length=MAX_STATIONS)
    mode: DeviceMode | None = None


class StationOptionOut(BaseModel):
    id: str
    name: str
    kind: StationKind
    # Tablet terdaftar di cabang yang memegang stasiun ini; kosong berarti stasiun ini belum aktif di cabang itu.
    device_names: list[str]
    # Semua tablet cabang ini (terdaftar atau menunggu) yang memegang stasiun ini, dan yang mencetaknya dari kasir (Mode Kasir).
    holder_device_ids: list[str]
    printer_device_ids: list[str]


class DeviceOut(BaseModel):
    id: str
    outlet_id: str
    outlet_name: str
    name: str
    section: str
    status: str
    mode: DeviceMode
    android_id: str | None
    serial: str | None
    brand: str | None
    model: str | None
    # Nama admin yang menambahkan perangkat; kosong bila akunnya sudah tidak ada.
    registered_by_name: str | None
    created_at: datetime
    paired_at: datetime | None
    last_used_at: datetime | None
    station_ids: list[str]
    station_names: list[str]
    print_station_ids: list[str]
    print_station_names: list[str]


class DeviceCodeOut(DeviceOut):
    code: str = Field(description="Shown once; afterwards only its hash exists on the server")
    code_expires_at: datetime
