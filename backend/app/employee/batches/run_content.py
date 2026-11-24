"""Isi satu pengisian tugas outlet atau rutin: kepala dan jawabannya, dibaca admin di Riwayat dan karyawan dari tugas tindak lanjut."""
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.user_names import user_names
from app.employee.batches.constants import KIND_TOGGLE, TOGGLE_PROBLEM
from app.models.outlet import Outlet
from app.models.outlet_batch import OutletBatch, OutletBatchAnswer, OutletBatchItem, OutletBatchRun


@dataclass(frozen=True)
class AnswerRow:
    label: str
    kind: str
    value: str | None
    photo_path: str | None


@dataclass(frozen=True)
class RunContent:
    id: str
    kind: str
    day: date
    completed_at: datetime
    batch_name: str
    outlet_name: str
    completer_name: str | None
    answers: list[AnswerRow]

    @property
    def problems(self) -> int:
        return problem_count(self.answers)


def problem_count(answers: list[AnswerRow]) -> int:
    return sum(1 for answer in answers if answer.kind == KIND_TOGGLE and answer.value == TOGGLE_PROBLEM)


def answers_of(db: Session, run_id: str) -> list[AnswerRow]:
    """Berurutan seperti isian di templatnya; jawaban yang isiannya sudah dihapus berada di akhir."""
    rows = db.execute(
        select(OutletBatchAnswer.item_label, OutletBatchAnswer.item_kind, OutletBatchAnswer.value, OutletBatchAnswer.photo_path)
        .outerjoin(OutletBatchItem, OutletBatchItem.id == OutletBatchAnswer.item_id)
        .where(OutletBatchAnswer.run_id == run_id)
        .order_by(OutletBatchItem.position.asc().nulls_last(), OutletBatchAnswer.id)
    ).all()
    return [AnswerRow(label=label, kind=kind, value=value, photo_path=path) for label, kind, value, path in rows]


def run_content(db: Session, run_id: str) -> RunContent | None:
    row = db.execute(
        select(OutletBatchRun.id, OutletBatch.kind, OutletBatchRun.day, OutletBatchRun.completed_at, OutletBatch.name, Outlet.name, OutletBatchRun.completed_by_id)
        .join(OutletBatch, OutletBatch.id == OutletBatchRun.batch_id)
        .join(Outlet, Outlet.id == OutletBatch.outlet_id)
        .where(OutletBatchRun.id == run_id)
    ).first()
    if row is None:
        return None
    found_id, kind, day, completed_at, batch_name, outlet_name, completer_id = row
    return RunContent(
        id=found_id,
        kind=kind,
        day=day,
        completed_at=completed_at,
        batch_name=batch_name,
        outlet_name=outlet_name,
        completer_name=user_names(db, [completer_id]).get(completer_id) if completer_id else None,
        answers=answers_of(db, found_id),
    )
