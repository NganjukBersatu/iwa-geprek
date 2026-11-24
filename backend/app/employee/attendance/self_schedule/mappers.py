"""Turns the self-made schedule options into response schemas."""
from app.employee.attendance.self_schedule.domain import Options, Suggestion
from app.employee.attendance.self_schedule.schemas import SelfScheduleChoiceOut, SelfScheduleOptionsOut, SuggestionOut


def _suggestion_out(item: Suggestion) -> SuggestionOut:
    return SuggestionOut(
        shift_code_id=item.code.id,
        code=item.code.code,
        color=item.code.color,
        date=item.day,
        starts_at=item.starts_at,
        ends_at=item.ends_at,
    )


def options_out(options: Options) -> SelfScheduleOptionsOut:
    return SelfScheduleOptionsOut(
        outlets=[SelfScheduleChoiceOut(id=outlet.id, name=outlet.name) for outlet in options.outlets],
        roles=[SelfScheduleChoiceOut(id=role.id, name=role.name) for role in options.roles],
        suggestions=[_suggestion_out(item) for item in options.suggestions],
    )
