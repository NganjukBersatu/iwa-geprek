"""Each function returns up to [limit] of one source's newest events before [before], newest first."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import as_aware, minutes_between
from app.employee.activity.constants import AUTO_STATUS
from app.employee.activity.domain import Action, Event
from app.models.attendance import Attendance
from app.models.cash_session import CashSession
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.order import Order
from app.models.overtime import Overtime
from app.models.task import Task, TaskStatus


def attendance(db: Session, user_id: str, before: datetime | None, limit: int) -> list[Event]:
    events: list[Event] = []
    for column, action in ((Attendance.clock_in_at, Action.CLOCK_IN), (Attendance.clock_out_at, Action.CLOCK_OUT)):
        query = select(Attendance).where(Attendance.user_id == user_id, column.is_not(None))
        if before is not None:
            query = query.where(column < before)
        for record in db.scalars(query.order_by(column.desc()).limit(limit)).all():
            if action is Action.CLOCK_IN:
                events.append(Event(f"in:{record.id}", action, as_aware(record.clock_in_at), status=record.status.value))
            else:
                events.append(
                    Event(
                        f"out:{record.id}",
                        action,
                        as_aware(record.clock_out_at),
                        status=AUTO_STATUS if record.auto_closed else None,
                    )
                )
    return events


def tasks(db: Session, user_id: str, before: datetime | None, limit: int) -> list[Event]:
    query = select(Task).where(
        Task.assignee_id == user_id, Task.status == TaskStatus.DONE, Task.completed_at.is_not(None)
    )
    if before is not None:
        query = query.where(Task.completed_at < before)
    return [
        Event(f"task:{task.id}", Action.TASK_DONE, as_aware(task.completed_at), subject=task.title)
        for task in db.scalars(query.order_by(Task.completed_at.desc()).limit(limit)).all()
    ]


def overtime(db: Session, user_id: str, before: datetime | None, limit: int) -> list[Event]:
    query = select(Overtime).where(Overtime.user_id == user_id, Overtime.end_at.is_not(None))
    if before is not None:
        query = query.where(Overtime.created_at < before)
    return [
        Event(
            f"overtime:{item.id}",
            Action.OVERTIME_RECORDED,
            as_aware(item.created_at),
            minutes=minutes_between(item.start_at, item.end_at),
        )
        for item in db.scalars(query.order_by(Overtime.created_at.desc()).limit(limit)).all()
    ]


def leave(db: Session, user_id: str, before: datetime | None, limit: int) -> list[Event]:
    events: list[Event] = []
    requested = select(LeaveRequest).where(LeaveRequest.user_id == user_id)
    decided = select(LeaveRequest).where(
        LeaveRequest.user_id == user_id,
        LeaveRequest.decided_at.is_not(None),
        LeaveRequest.status != LeaveStatus.PENDING,
    )
    if before is not None:
        requested = requested.where(LeaveRequest.created_at < before)
        decided = decided.where(LeaveRequest.decided_at < before)
    for item in db.scalars(requested.order_by(LeaveRequest.created_at.desc()).limit(limit)).all():
        events.append(Event(f"leave:{item.id}", Action.LEAVE_REQUESTED, as_aware(item.created_at), subject=item.type.value))
    for item in db.scalars(decided.order_by(LeaveRequest.decided_at.desc()).limit(limit)).all():
        events.append(
            Event(
                f"leave-decision:{item.id}",
                Action.LEAVE_DECIDED,
                as_aware(item.decided_at),
                subject=item.type.value,
                status=item.status.value,
            )
        )
    return events


def operations(db: Session, user_id: str, before: datetime | None, limit: int) -> list[Event]:
    events: list[Event] = []

    created = select(Order).where(Order.cashier_id == user_id)
    voided = select(Order).where(Order.voided_by_id == user_id, Order.voided_at.is_not(None))
    opened = select(CashSession).where(CashSession.cashier_id == user_id)
    closed = select(CashSession).where(CashSession.cashier_id == user_id, CashSession.closed_at.is_not(None))
    if before is not None:
        created = created.where(Order.created_at < before)
        voided = voided.where(Order.voided_at < before)
        opened = opened.where(CashSession.opened_at < before)
        closed = closed.where(CashSession.closed_at < before)

    for order in db.scalars(created.order_by(Order.created_at.desc()).limit(limit)).all():
        events.append(Event(f"order:{order.id}", Action.ORDER_CREATED, as_aware(order.created_at), subject=order.receipt_number))
    for order in db.scalars(voided.order_by(Order.voided_at.desc()).limit(limit)).all():
        events.append(Event(f"order-void:{order.id}", Action.ORDER_VOIDED, as_aware(order.voided_at), subject=order.receipt_number))
    for session in db.scalars(opened.order_by(CashSession.opened_at.desc()).limit(limit)).all():
        events.append(Event(f"cash-open:{session.id}", Action.CASH_OPENED, as_aware(session.opened_at), subject=session.shift_code))
    for session in db.scalars(closed.order_by(CashSession.closed_at.desc()).limit(limit)).all():
        events.append(Event(f"cash-close:{session.id}", Action.CASH_CLOSED, as_aware(session.closed_at), subject=session.shift_code))
    return events
