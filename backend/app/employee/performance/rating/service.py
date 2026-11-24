"""Scores behavior (on time, attendance) and work (given and own tasks, done and in time) into a half-star rating."""
import math
from datetime import datetime

from app.core.clock import as_aware
from app.employee.attendance.summary.domain import Day
from app.employee.performance.constants import PERCENT
from app.employee.performance.rating import constants
from app.employee.performance.rating.scheduled import Key
from app.employee.performance.rating.domain import Component, Group, Rating
from app.models.attendance import AttendanceStatus
from app.models.task import Task, TaskStatus

HERE = AttendanceStatus.PRESENT
LATE = AttendanceStatus.LATE
ABSENT = AttendanceStatus.ABSENT


def _component(key: str, counted: int, of: int, enough: bool = True) -> Component:
    percent = PERCENT * counted / of if enough and of > 0 else None
    return Component(key, percent, counted, of)


def _score(components: list[Component]) -> float | None:
    known = [component.percent for component in components if component.percent is not None]
    return sum(known) / len(known) if known else None


def _behavior(days: list[Day], scheduled: dict[Key, int]) -> Group:
    """On time counts days; attendance counts scheduled minutes, losing only those of absent days."""
    present_days = sum(1 for day in days if day.status in (HERE, LATE))
    on_time_days = sum(1 for day in days if day.status == HERE)
    counted = [
        (day, scheduled[(day.date, day.code)])
        for day in days
        if day.status in (HERE, LATE, ABSENT) and (day.date, day.code) in scheduled
    ]
    total = sum(minutes for _, minutes in counted)
    lost = sum(minutes for day, minutes in counted if day.status == ABSENT)
    components = [
        _component(constants.ON_TIME, on_time_days, present_days, present_days >= constants.MIN_COUNTED_DAYS),
        _component(constants.ATTENDANCE, total - lost, total, len(counted) >= constants.MIN_COUNTED_DAYS),
    ]
    return Group(constants.BEHAVIOR, _score(components), components)


def _task_components(tasks: list[Task], at: datetime, done_key: str, in_time_key: str) -> list[Component]:
    """A task counts once it has an outcome: done, or still open after its due time; until then it is left out."""
    done = [task for task in tasks if task.status == TaskStatus.DONE and task.completed_at is not None]
    overdue = [
        task
        for task in tasks
        if task.status != TaskStatus.DONE and task.due_at is not None and as_aware(task.due_at) < at
    ]
    done_with_due = [task for task in done if task.due_at is not None]
    in_time = sum(1 for task in done_with_due if as_aware(task.completed_at) <= as_aware(task.due_at))
    return [
        _component(done_key, len(done), len(done) + len(overdue)),
        _component(in_time_key, in_time, len(done_with_due) + len(overdue)),
    ]


def _work(user_id: str, tasks: list[Task], at: datetime) -> Group:
    """Tasks the person made for themselves are scored apart from those given by someone else."""
    # A missing creator was another account: a self-made task is deleted together with its maker.
    own = [task for task in tasks if task.creator_id == user_id]
    given = [task for task in tasks if task.creator_id != user_id]
    components = [
        *_task_components(given, at, constants.GIVEN_TASKS_DONE, constants.GIVEN_TASKS_IN_TIME),
        *_task_components(own, at, constants.OWN_TASKS_DONE, constants.OWN_TASKS_IN_TIME),
    ]
    return Group(constants.WORK, _score(components), components)


def _overall(groups: list[Group]) -> float | None:
    weighted = [(group.score, constants.WEIGHTS[group.key]) for group in groups if group.score is not None]
    total = sum(weight for _, weight in weighted)
    return sum(score * weight for score, weight in weighted) / total if total else None


def _stars(score: float) -> float:
    steps = score / PERCENT * constants.MAX_STARS / constants.STAR_STEP
    return math.floor(steps + 0.5) * constants.STAR_STEP


def build(user_id: str, days: list[Day], tasks: list[Task], scheduled: dict[Key, int], at: datetime) -> Rating:
    """`at` is the moment the rating is read; a due time is judged against it, as the task list shows it."""
    groups = [_behavior(days, scheduled), _work(user_id, tasks, at)]
    score = _overall(groups)
    return Rating(stars=None if score is None else _stars(score), score=score, groups=groups)


def empty() -> Rating:
    return Rating(stars=None, score=None, groups=[])
