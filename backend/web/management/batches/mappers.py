"""Turns batches into the admin's response schemas."""
from app.core.http import static_url
from app.employee.batches import recurrence
from app.employee.batches.mappers import item_out
from app.models.outlet_batch import OutletBatch
from app.models.shift_code import ShiftCode
from app.models.user import User
from web.management.batches.domain import CopyOutcome
from app.employee.batches.run_content import AnswerRow
from web.management.batches.history import FollowUpRow, RunPage, RunRow, VersionRow
from web.management.batches.schemas import (
    AnswerOut,
    BatchCopyCreatedOut,
    BatchCopyOut,
    BatchCopySkippedOut,
    BatchUserOut,
    BatchUserPageOut,
    FollowUpOut,
    ManagedBatchListOut,
    ManagedBatchOut,
    RunDetailOut,
    RunOut,
    RunPageOut,
    RunVersionOut,
    BatchShiftCodeListOut,
    BatchShiftCodeOut,
)



def shift_code_out(code: ShiftCode) -> BatchShiftCodeOut:
    return BatchShiftCodeOut(id=code.id, code=code.code, color=code.color, start_clock=code.start_clock, end_clock=code.end_clock)


def shift_code_list_out(codes: list[ShiftCode]) -> BatchShiftCodeListOut:
    return BatchShiftCodeListOut(items=[shift_code_out(code) for code in codes])


def user_out(person: User) -> BatchUserOut:
    return BatchUserOut(id=person.id, name=person.name or person.username, role_name=person.role.name if person.role else None)


def user_page_out(people: list[User], total: int, page: int, size: int) -> BatchUserPageOut:
    return BatchUserPageOut(items=[user_out(person) for person in people], total=total, page=page, size=size)


def copy_out(outcomes: list[CopyOutcome], names: dict[str, str]) -> BatchCopyOut:
    return BatchCopyOut(
        created=[BatchCopyCreatedOut(outlet_id=o.outlet_id, outlet_name=names.get(o.outlet_id, ""), batch_id=o.batch_id) for o in outcomes if o.batch_id],
        skipped=[BatchCopySkippedOut(outlet_id=o.outlet_id, outlet_name=names.get(o.outlet_id, ""), reason=o.reason or "") for o in outcomes if not o.batch_id],
    )


def managed_out(batch: OutletBatch, outlet_name: str) -> ManagedBatchOut:
    return ManagedBatchOut(
        id=batch.id,
        outlet_id=batch.outlet_id,
        outlet_name=outlet_name,
        kind=batch.kind,
        fill_mode=batch.fill_mode,
        shift_codes=[shift_code_out(code) for code in batch.shift_codes],
        target=batch.target,
        user=[user_out(person) for person in batch.recipients],
        name=batch.name,
        start_clock=batch.start_clock,
        end_clock=batch.end_clock,
        repeat_unit=batch.repeat_unit,
        repeat_every=batch.repeat_every,
        starts_on=batch.starts_on,
        weekdays=sorted(recurrence.numbers_of(batch.weekdays)),
        is_active=batch.is_active,
        items=[item_out(item) for item in batch.items],
    )


def run_out(run: RunRow) -> RunOut:
    return RunOut(
        id=run.id,
        kind=run.kind,
        day=run.day,
        completed_at=run.completed_at,
        batch_name=run.batch_name,
        outlet_id=run.outlet_id,
        outlet_name=run.outlet_name,
        completed_by=run.completer_name,
        problems=run.problems,
        follow_up_total=run.follow_up_total,
        follow_up_open=run.follow_up_open,
        cancelled=run.cancelled,
        version_count=run.version_count,
        fixed_by=run.fixed_by,
        fixed_at=run.fixed_at,
        last_action=run.last_action,
    )


def run_page_out(page: RunPage, page_number: int, size: int) -> RunPageOut:
    return RunPageOut(items=[run_out(run) for run in page.items], total=page.total, page=page_number, size=size)


def _answers_out(answers: list[AnswerRow], base_url: str) -> list[AnswerOut]:
    return [AnswerOut(label=answer.label, kind=answer.kind, value=answer.value, photo_url=static_url(base_url, answer.photo_path)) for answer in answers]


def run_detail_out(run: RunRow, answers: list[AnswerRow], follow_ups: list[FollowUpRow], versions: list[VersionRow], base_url: str) -> RunDetailOut:
    return RunDetailOut(
        **run_out(run).model_dump(),
        answers=_answers_out(answers, base_url),
        versions=[
            RunVersionOut(
                number=version.number,
                action=version.action,
                changed_by=version.changed_by,
                changed_at=version.changed_at,
                completed_by=version.completed_by,
                completed_at=version.completed_at,
                answers=_answers_out(version.answers, base_url),
            )
            for version in versions
        ],
        follow_ups=[
            FollowUpOut(
                task_id=row.task_id,
                number=row.number,
                title=row.title,
                assignee_name=row.assignee_name,
                done=row.done,
                due_at=row.due_at,
                completed_at=row.completed_at,
                created_at=row.created_at,
            )
            for row in follow_ups
        ],
    )


def managed_list_out(batches: list[OutletBatch], names: dict[str, str], total: int, page: int, size: int) -> ManagedBatchListOut:
    return ManagedBatchListOut(items=[managed_out(batch, names.get(batch.outlet_id, "")) for batch in batches], total=total, page=page, size=size)
