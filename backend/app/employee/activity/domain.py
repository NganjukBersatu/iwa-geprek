from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Group(str, Enum):
    ATTENDANCE = "attendance"
    TASK = "task"
    OVERTIME = "overtime"
    LEAVE = "leave"
    OPERATIONS = "operations"


class Action(str, Enum):
    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"
    TASK_DONE = "task_done"
    OVERTIME_RECORDED = "overtime_recorded"
    LEAVE_REQUESTED = "leave_requested"
    LEAVE_DECIDED = "leave_decided"
    ORDER_CREATED = "order_created"
    ORDER_VOIDED = "order_voided"
    CASH_OPENED = "cash_opened"
    CASH_CLOSED = "cash_closed"


GROUP_OF_ACTION = {
    Action.CLOCK_IN: Group.ATTENDANCE,
    Action.CLOCK_OUT: Group.ATTENDANCE,
    Action.TASK_DONE: Group.TASK,
    Action.OVERTIME_RECORDED: Group.OVERTIME,
    Action.LEAVE_REQUESTED: Group.LEAVE,
    Action.LEAVE_DECIDED: Group.LEAVE,
    Action.ORDER_CREATED: Group.OPERATIONS,
    Action.ORDER_VOIDED: Group.OPERATIONS,
    Action.CASH_OPENED: Group.OPERATIONS,
    Action.CASH_CLOSED: Group.OPERATIONS,
}


@dataclass(frozen=True)
class Event:
    id: str
    action: Action
    at: datetime
    # Task title, receipt number, shift code, or leave type, whichever the action is about.
    subject: str | None = None
    # Attendance status, leave decision, or "auto" for a clock-out the system made.
    status: str | None = None
    minutes: int | None = None

    @property
    def group(self) -> Group:
        return GROUP_OF_ACTION[self.action]


@dataclass(frozen=True)
class Page:
    events: list[Event]
    # Pass this as `before` to get the next older page; None when there is nothing older.
    next_before: datetime | None
