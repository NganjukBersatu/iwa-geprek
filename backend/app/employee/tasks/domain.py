"""What the task service hands to the mappers."""
from dataclasses import dataclass
from datetime import date, datetime

from app.models.outlet import Outlet
from app.models.user import User


@dataclass(frozen=True)
class AttachmentEntry:
    id: str
    kind: str
    path: str
    removable: bool


@dataclass(frozen=True)
class SourceRun:
    """Pengisian tugas outlet atau rutin yang ditindaklanjuti sebuah tugas."""

    id: str
    batch_name: str
    kind: str
    day: date
    outlet_id: str


@dataclass(frozen=True)
class FollowUpPlace:
    """Urutan sebuah tugas di antara semua tindak lanjut pengisian yang sama, menurut waktu dibuat."""

    number: int
    total: int


@dataclass(frozen=True)
class TaskEntry:
    id: str
    outlet_id: str | None
    outlet_name: str | None
    title: str
    description: str | None
    assignee: User | None
    creator: User | None
    completer: User | None
    due_at: datetime | None
    done: bool
    completion_note: str | None
    completed_at: datetime | None
    created_at: datetime
    attachments: tuple[AttachmentEntry, ...]
    source_run: SourceRun | None
    follow_up: FollowUpPlace | None

    @property
    def assignee_id(self) -> str | None:
        return self.assignee.id if self.assignee else None

    @property
    def creator_id(self) -> str | None:
        return self.creator.id if self.creator else None


@dataclass(frozen=True)
class TaskPage:
    items: list[TaskEntry]
    total: int
    page: int
    size: int


@dataclass(frozen=True)
class TaskQuery:
    """What a task list is narrowed to; only the status is always present.

    `start` and `end` bound the day a task belongs to (`end` exclusive): the day it was finished for a finished
    task, otherwise its deadline or, without one, the day it was created.
    """

    done: bool
    start: datetime | None = None
    end: datetime | None = None
    outlet_id: str | None = None
    search: str | None = None
    assignee_id: str | None = None


@dataclass(frozen=True)
class NewTask:
    title: str
    description: str | None
    assignee_id: str | None
    due_at: datetime | None
    complete: bool
    source_run_id: str | None = None


@dataclass(frozen=True)
class TaskChanges:
    title: str | None
    description: str | None
    due_at: datetime | None


@dataclass(frozen=True)
class TaskOptions:
    outlets: list[Outlet]
    assignees: list[User]
    can_manage: bool
