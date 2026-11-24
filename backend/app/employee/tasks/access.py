"""Who may change or finish a task; the service asks here and never decides alone."""
from app.employee.tasks.constants import PERMISSION_MANAGE
from app.models.user import User


def is_manager(user: User) -> bool:
    return user.allows(PERMISSION_MANAGE)


def can_edit(user: User, creator_id: str | None) -> bool:
    """Only what a person created is theirs to change; a manager may change anything."""
    return is_manager(user) or (creator_id is not None and creator_id == user.id)


def can_complete(user: User, done: bool, assignee_id: str | None) -> bool:
    """A task is finished by the person it is given to."""
    return not done and assignee_id == user.id


def can_fix(user: User, done: bool, assignee_id: str | None) -> bool:
    """Yang sudah dikirim boleh dibenahi pengirimnya: catatan selesai dan buktinya."""
    return done and (assignee_id == user.id or is_manager(user))


def can_delete(user: User, done: bool, assignee_id: str | None, creator_id: str | None) -> bool:
    """Pembuat dan pengelola kapan pun; penerima hanya setelah tugasnya ia selesaikan, supaya tugas yang belum dikerjakan tidak bisa dibuang."""
    return can_edit(user, creator_id) or (done and assignee_id == user.id)
