"""Database reads for the performance charts, each one query however many people are asked for."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.schedule import Schedule
from app.models.task import Task


def first_activity_dates(db: Session, user_ids: list[str]) -> dict[str, date]:
    """The earliest day each person has an attendance record or a schedule."""
    if not user_ids:
        return {}
    found: dict[str, date] = {}
    for model in (Attendance, Schedule):
        rows = db.execute(select(model.user_id, func.min(model.date)).where(model.user_id.in_(user_ids)).group_by(model.user_id)).all()
        for user_id, day in rows:
            if day is not None and (user_id not in found or day < found[user_id]):
                found[user_id] = day
    return found


def assigned_tasks_many(db: Session, user_ids: list[str]) -> dict[str, list[Task]]:
    found: dict[str, list[Task]] = {user_id: [] for user_id in user_ids}
    if not user_ids:
        return found
    for task in db.scalars(select(Task).where(Task.assignee_id.in_(user_ids))).all():
        found[task.assignee_id].append(task)
    return found
