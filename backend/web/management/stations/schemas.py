from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.orders.station_setup import MAX_NAME_LENGTH, MAX_TARGET_SECONDS
from app.core.orders.stations import MAX_REASON_LENGTH, Stage
from app.models.station import StationKind

Target = int | None
MAX_BRANCHES = 500
MAX_ROLES_PER_BRANCH = 50


class StationCreateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    kind: StationKind
    target_seconds: Target = Field(None, ge=1, le=MAX_TARGET_SECONDS)


class StationPatchIn(BaseModel):
    # Hanya field yang dikirim yang diubah (rules 17.2).
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=1, max_length=MAX_NAME_LENGTH)
    kind: StationKind | None = None
    target_seconds: Target = Field(None, ge=1, le=MAX_TARGET_SECONDS)


class StationBranchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outlet_id: str = Field(min_length=1, max_length=64)
    # Kosong berarti sama dengan target semua cabang; hanya dipakai stasiun pengantar.
    target_seconds: Target = Field(None, ge=1, le=MAX_TARGET_SECONDS)
    # Jeda bunyi pengingat dalam detik; 0 mematikan pengingat, selain itu 15 detik sampai 10 menit; tidak dikirim berarti tidak diubah.
    reminder_seconds: int | None = Field(None, ge=0, le=600)
    # Peran jadwal yang mengerjakan stasiun ini di cabang itu; kosong berarti ikut peran bawaan stasiun; tidak dikirim berarti tidak diubah.
    role_ids: list[str] | None = Field(None, max_length=MAX_ROLES_PER_BRANCH)


class StationBranchesIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    branches: list[StationBranchIn] = Field(min_length=1, max_length=MAX_BRANCHES)


class StationRolesIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_ids: list[str] = Field(max_length=MAX_ROLES_PER_BRANCH)


class StationRolesOut(BaseModel):
    role_ids: list[str]


class StationBranchOut(BaseModel):
    outlet_id: str
    outlet_name: str
    used: bool
    target_seconds: Target
    reminder_seconds: int
    role_ids: list[str]


class CategoryStationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_id: str | None


class CategoryBranchStationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    follows_default: bool
    station_id: str | None = None


class StationBranchCopyIn(BaseModel):
    """Menyalin pengaturan stasiun dari satu cabang ke cabang pilihan dalam satu transaksi."""

    model_config = ConfigDict(extra="forbid")

    from_outlet_id: str = Field(min_length=1)
    to_outlet_ids: list[str] = Field(min_length=1, max_length=MAX_BRANCHES)


class MenuTargetIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_seconds: Target = Field(None, ge=1, le=MAX_TARGET_SECONDS)


class StationInterveneIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(pattern="^(start|finish|undo)$")
    seen: Stage
    reason: str = Field(min_length=1, max_length=MAX_REASON_LENGTH)


class ManagedStationOut(BaseModel):
    id: str
    name: str
    kind: StationKind
    target_seconds: Target
    # Nilai milik cabang terpilih; kosong berarti ikut bawaan di atas.
    used: bool
    branch_target_seconds: Target
    categories: list[str]


class CategoryBranchOut(BaseModel):
    outlet_id: str
    outlet_name: str
    # Kosong berarti di cabang ini kategori langsung diantar tanpa stasiun pembuat.
    station_id: str | None


class StationCategoryOut(BaseModel):
    id: str
    name: str
    station_id: str | None
    # Cabang yang memakai stasiun berbeda dari semua cabang, urut nama cabang.
    branches: list[CategoryBranchOut]


class StationSetupOut(BaseModel):
    outlet_id: str | None
    stations: list[ManagedStationOut]
    categories: list[StationCategoryOut]


class StationMonitorCellOut(BaseModel):
    station_id: str
    working: int
    late: int


class StationMonitorBranchOut(BaseModel):
    outlet_id: str
    outlet_name: str
    cells: list[StationMonitorCellOut]


class StationLateTaskOut(BaseModel):
    task_id: str
    order_id: str
    receipt_number: str | None
    table_no: str | None
    customer_name: str | None
    outlet_name: str
    station_name: str
    item: str
    stage: Stage
    started_at: datetime | None
    target_seconds: int | None
    late_seconds: int


class StationMonitorOut(BaseModel):
    stations: list[ManagedStationOut]
    branches: list[StationMonitorBranchOut]
    working: int
    late: int
    late_tasks: list[StationLateTaskOut]


class StationStepOut(BaseModel):
    step: str
    by: str | None
    reason: str | None
    intervened: bool
    at: datetime


class StationTaskOut(BaseModel):
    task_id: str
    order_id: str
    receipt_number: str | None
    table_no: str | None
    customer_name: str | None
    order_created_at: datetime
    outlet_name: str
    station_name: str
    station_kind: StationKind
    item: str
    note: str | None
    options: list[str]
    stage: Stage
    arrived_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    target_seconds: int | None
    removed: bool
    voided: bool
    locked: bool
    steps: list[StationStepOut]


class StationTimingOut(BaseModel):
    tasks: int
    average_wait_seconds: Decimal | None
    average_work_seconds: Decimal | None
    on_time_ratio: Decimal | None


class StationHourOut(StationTimingOut):
    hour: int


class StationUserTimingOut(StationTimingOut):
    user_id: str | None
    name: str
    station_id: str
    station_name: str


class StationNameOut(BaseModel):
    id: str
    name: str


class StationPerformanceOut(BaseModel):
    start: date
    end: date
    # Daftar stasiun untuk pilihan filter, karena pembaca laporan belum tentu boleh membuka pengaturan stasiun.
    stations: list[StationNameOut]
    overall: StationTimingOut
    by_hour: list[StationHourOut]
    by_user: list[StationUserTimingOut]


class MenuTargetRowOut(StationTimingOut):
    menu_id: str
    name: str
    station_name: str | None
    target_seconds: Target
    branch_target_seconds: Target


class MenuTargetPageOut(BaseModel):
    start: date
    end: date
    items: list[MenuTargetRowOut]
    total: int
    page: int
    size: int


class MenuTargetBranchOut(StationTimingOut):
    outlet_id: str
    outlet_name: str
    target_seconds: Target


class MenuTargetDetailOut(BaseModel):
    start: date
    end: date
    menu_id: str
    name: str
    station_name: str | None
    target_seconds: Target
    overall: StationTimingOut
    branches: list[MenuTargetBranchOut]
    by_hour: list[StationHourOut]
