"""Who may open a stored file outside the public folders: its owner, or user holding the right for that record's branch."""
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PurePosixPath
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.storage import folders
from app.models.attendance import Attendance
from app.models.deposit import Deposit
from app.models.device import Device
from app.models.expense import Expense
from app.models.ingredient import IngredientCard
from app.models.leave_request import LeaveRequest
from app.models.outlet_batch import OutletBatch, OutletBatchAnswer, OutletBatchRun
from app.models.user import User
from app.models.task import Task
from app.models.task_attachment import TaskAttachment

PATH_DEPTH_WITH_OWNER_FOLDER = 3
PATH_DEPTH_FLAT = 2
# A receipt shared by one purchase of several items is found by its path; a purchase never has more lines than this.
MAX_SHARED_RECEIPT_ROWS = 50

PERMISSION_VIEW_ALL_EXPENSES = "pengeluaran.lihat_semua"
PERMISSION_VIEW_DEPOSITS = "setoran.lihat"
PERMISSION_VIEW_STOCK = "stok.lihat"
PERMISSION_MANAGE_ATTENDANCE = "kehadiran.kelola"
PERMISSION_MANAGE_USER = "karyawan.kelola"
PERMISSION_VIEW_SCHEDULE = "jadwal.lihat"
PERMISSION_VIEW_TASKS = "tugas.lihat"


@dataclass(frozen=True)
class _Record:
    """The record a file belongs to: its branch, the person it is about, and the rights that open it for anyone else."""

    outlet_id: str | None
    owner_id: str | None
    rights: tuple[str, ...]


def _receipt(db: Session, parts: list[str], path: str) -> list[_Record]:
    if len(parts) != PATH_DEPTH_WITH_OWNER_FOLDER:
        return []
    if parts[1] == folders.SHARED_RECEIPT:
        rows = db.scalars(select(Expense).where(Expense.receipt_path == path).limit(MAX_SHARED_RECEIPT_ROWS)).all()
    else:
        expense = db.get(Expense, parts[1])
        rows = [expense] if expense is not None and expense.receipt_path == path else []
    return [_Record(row.outlet_id, row.cashier_id, (PERMISSION_VIEW_ALL_EXPENSES,)) for row in rows]


def _deposit(db: Session, parts: list[str], path: str) -> list[_Record]:
    deposit = db.get(Deposit, parts[1]) if len(parts) == PATH_DEPTH_WITH_OWNER_FOLDER else None
    if deposit is None or deposit.photo_path != path:
        return []
    return [_Record(deposit.outlet_id, deposit.user_id, (PERMISSION_VIEW_DEPOSITS,))]


def _ingredient_proof(db: Session, parts: list[str], path: str) -> list[_Record]:
    card = db.get(IngredientCard, parts[1]) if len(parts) == PATH_DEPTH_WITH_OWNER_FOLDER else None
    if card is None or card.proof_path != path:
        return []
    return [_Record(card.outlet_id, card.user_id, (PERMISSION_VIEW_STOCK,))]


def _profile(db: Session, parts: list[str], path: str) -> list[_Record]:
    user = db.get(User, parts[1]) if len(parts) == PATH_DEPTH_WITH_OWNER_FOLDER else None
    if user is None or user.photo_key != path:
        return []
    return [_Record(user.outlet_id, user.id, (PERMISSION_MANAGE_USER, PERMISSION_MANAGE_ATTENDANCE, PERMISSION_VIEW_SCHEDULE))]


def _flat_id(parts: list[str], suffix: str = "") -> str | None:
    """The record id a file named `<id><suffix>.<extension>` carries in its name."""
    if len(parts) != PATH_DEPTH_FLAT:
        return None
    return PurePosixPath(parts[1]).stem.removesuffix(suffix) or None


def _attendance(db: Session, parts: list[str], path: str) -> list[_Record]:
    record_id = _flat_id(parts, folders.CLOCK_OUT_PHOTO_SUFFIX)
    record = db.get(Attendance, record_id) if record_id else None
    if record is None or path not in (record.clock_in_photo_path, record.clock_out_photo_path):
        return []
    return [_Record(record.outlet_id, record.user_id, (PERMISSION_MANAGE_ATTENDANCE,))]


def _leave(db: Session, parts: list[str], path: str) -> list[_Record]:
    request_id = _flat_id(parts)
    request = db.get(LeaveRequest, request_id) if request_id else None
    if request is None or request.attachment_path != path:
        return []
    return [_Record(request.outlet_id, request.user_id, (PERMISSION_MANAGE_ATTENDANCE,))]


def _batch(db: Session, parts: list[str], path: str) -> list[_Record]:
    answer_id = PurePosixPath(parts[2]).stem if len(parts) == PATH_DEPTH_WITH_OWNER_FOLDER else None
    answer = db.get(OutletBatchAnswer, answer_id) if answer_id else None
    if answer is None or answer.photo_path != path or answer.run_id != parts[1]:
        return []
    run = db.get(OutletBatchRun, answer.run_id)
    batch = db.get(OutletBatch, run.batch_id) if run is not None else None
    if run is None or batch is None:
        return []
    return [_Record(batch.outlet_id, run.completed_by_id, (PERMISSION_VIEW_TASKS,))]


def _task_media(db: Session, parts: list[str], path: str) -> list[_Record]:
    """Foto tugas dibuka penerima, pembuat, dan pemegang izin lihat tugas di cabangnya."""
    if len(parts) != PATH_DEPTH_WITH_OWNER_FOLDER:
        return []
    try:
        task_id = str(UUID(parts[1]))
    except ValueError:
        return []
    attachment = db.get(TaskAttachment, PurePosixPath(parts[2]).stem)
    task = db.get(Task, task_id)
    if attachment is None or attachment.path != path or task is None:
        return []
    owners = {task.assignee_id, task.creator_id} - {None}
    return [_Record(task.outlet_id, owner, (PERMISSION_VIEW_TASKS,)) for owner in owners] or [_Record(task.outlet_id, None, (PERMISSION_VIEW_TASKS,))]


_RESOLVERS: dict[str, Callable[[Session, list[str], str], list[_Record]]] = {
    folders.TASK_MEDIA: _task_media,
    folders.RECEIPT: _receipt,
    folders.DEPOSIT_PHOTO: _deposit,
    folders.INGREDIENT_PROOF: _ingredient_proof,
    folders.PROFILE_PHOTO: _profile,
    folders.ATTENDANCE_PHOTO: _attendance,
    folders.LEAVE_ATTACHMENT: _leave,
    folders.BATCH_PHOTO: _batch,
}


def _records(db: Session, path: str) -> list[_Record]:
    parts = path.split("/")
    resolver = _RESOLVERS.get(parts[0])
    return resolver(db, parts, path) if resolver is not None else []


def _user_may_open(user: User, record: _Record) -> bool:
    if record.owner_id == user.id:
        return True
    in_branch = user.locked_outlet_id is None or record.outlet_id is None or record.outlet_id == user.locked_outlet_id
    return in_branch and any(user.allows(right) for right in record.rights)


def user_may_read(db: Session, user: User, path: str) -> bool:
    return any(_user_may_open(user, record) for record in _records(db, path))


def device_may_read(db: Session, device: Device, path: str) -> bool:
    """A paired tablet shows the receipts of its own branch and nothing else."""
    if path.split("/")[0] != folders.RECEIPT:
        return False
    return any(record.outlet_id == device.outlet_id for record in _records(db, path))
