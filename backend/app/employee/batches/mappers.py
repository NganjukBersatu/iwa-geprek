"""Turns batches into response schemas."""
from app.core.http import static_url
from app.employee.batches.domain import BatchEntry, StoredAnswer
from app.employee.batches.schemas import BatchListOut, BatchOut, ItemOut, StoredAnswerOut, StoredRunOut
from app.models.outlet_batch import OutletBatchItem


def item_out(item: OutletBatchItem) -> ItemOut:
    return ItemOut(id=item.id, label=item.label, kind=item.kind, required=item.required, position=item.position)


def batch_out(entry: BatchEntry) -> BatchOut:
    batch = entry.batch
    return BatchOut(
        id=batch.id,
        kind=batch.kind,
        fill_mode=batch.fill_mode,
        name=batch.name,
        start_clock=batch.start_clock,
        end_clock=batch.end_clock,
        completed=entry.completed,
        completed_at=entry.completed_at,
        completed_by=entry.completed_by,
        run_id=entry.run_id,
        can_fix=entry.can_fix,
        can_cancel=entry.can_cancel,
        can_delete=entry.can_delete,
        items=[item_out(item) for item in batch.items],
    )


def batch_list_out(entries: list[BatchEntry]) -> BatchListOut:
    return BatchListOut(items=[batch_out(entry) for entry in entries])


def stored_run_out(entry: BatchEntry, answers: list[StoredAnswer], base_url: str) -> StoredRunOut:
    return StoredRunOut(
        batch=batch_out(entry),
        answers=[StoredAnswerOut(item_id=answer.item_id, value=answer.value, photo_url=static_url(base_url, answer.photo_path)) for answer in answers],
    )
