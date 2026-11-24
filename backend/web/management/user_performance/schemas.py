from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

from app.employee.performance.schemas import PerformanceOut


class ListRange(StrEnum):
    """Daftar hanya per siklus supaya data yang dihitung tetap terbatas; seluruh riwayat dilihat di halaman satu karyawan."""

    CYCLE = "cycle"
    PREVIOUS = "previous"


class UserPerformanceRowOut(BaseModel):
    user_id: str
    name: str
    role_name: str | None
    outlet_name: str | None
    start: date
    end: date
    counted_days: int
    stars: float | None
    score: float | None
    on_time_percent: int | None = Field(description="Of the days present, late, or absent; empty without such days")
    on_time: int
    late: int
    leave: int
    absent: int
    work_minutes: int
    overtime_minutes: int
    tasks_done: int
    tasks_assigned: int


class UserPerformancePageOut(BaseModel):
    items: list[UserPerformanceRowOut]
    total: int
    page: int
    size: int


class UserPerformanceOut(BaseModel):
    user_id: str
    name: str
    role_name: str | None
    outlet_name: str | None
    performance: PerformanceOut
