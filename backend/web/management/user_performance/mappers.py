"""Turns measured user into the admin's response schemas."""
from app.employee.performance.constants import PERCENT
from app.employee.performance.mappers import performance_out
from web.management.user_performance.schemas import UserPerformanceOut, UserPerformanceRowOut
from web.management.user_performance.service import Measured


def _name(measured: Measured) -> str:
    return measured.user.name or measured.user.username


def _role(measured: Measured) -> str | None:
    return measured.user.role.name if measured.user.role else None


def _on_time_percent(measured: Measured) -> int | None:
    """Sama dengan grafik tepat waktu di app: dari hari hadir, telat, dan alpa; izin dan sakit tidak dihitung."""
    composition = measured.performance.composition
    counted = composition.on_time + composition.late + composition.absent
    return round(PERCENT * composition.on_time / counted) if counted else None


def row_out(measured: Measured) -> UserPerformanceRowOut:
    result = measured.performance
    composition = result.composition
    return UserPerformanceRowOut(
        user_id=measured.user.id,
        name=_name(measured),
        role_name=_role(measured),
        outlet_name=measured.outlet_name,
        start=result.start,
        end=result.end,
        counted_days=result.counted_days,
        stars=result.rating.stars,
        score=result.rating.score,
        on_time_percent=_on_time_percent(measured),
        on_time=composition.on_time,
        late=composition.late,
        leave=composition.leave,
        absent=composition.absent,
        work_minutes=sum(bucket.work_minutes for bucket in result.buckets),
        overtime_minutes=sum(bucket.overtime_minutes for bucket in result.buckets),
        tasks_done=result.tasks_done,
        tasks_assigned=result.tasks_assigned,
    )


def detail_out(measured: Measured) -> UserPerformanceOut:
    return UserPerformanceOut(
        user_id=measured.user.id,
        name=_name(measured),
        role_name=_role(measured),
        outlet_name=measured.outlet_name,
        performance=performance_out(measured.performance),
    )
