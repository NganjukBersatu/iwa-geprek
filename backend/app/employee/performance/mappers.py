from app.employee.performance.domain import Performance
from app.employee.performance.rating.mappers import rating_out
from app.employee.performance.schemas import BucketOut, CompositionOut, PerformanceOut


def performance_out(performance: Performance) -> PerformanceOut:
    return PerformanceOut(
        range=performance.range.value,
        start=performance.start,
        end=performance.end,
        counted_days=performance.counted_days,
        buckets=[BucketOut(**vars(bucket)) for bucket in performance.buckets],
        composition=CompositionOut(**vars(performance.composition)),
        tasks_assigned=performance.tasks_assigned,
        tasks_done=performance.tasks_done,
        rating=rating_out(performance.rating),
    )
