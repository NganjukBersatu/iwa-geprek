"""Reading procedures: the global ones and those of the reader's branch."""
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.clock import now
from app.core.errors import DomainError
from app.employee.sop import messages, repository
from app.models.sop import Sop, SopRead
from app.models.user import User

BAD_REQUEST = 400
NOT_FOUND = 404
BAD_REQUEST = 400
MEDIA_FOLDER = "sop"


def list_active(db: Session, user: User) -> list[Sop]:
    return repository.active(db, user.working_outlet_id)


def get_active(db: Session, user: User, sop_id: str) -> Sop:
    sop = repository.find_active(db, sop_id, user.working_outlet_id)
    if sop is None:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return sop


def outlet_names(db: Session, sops: list[Sop]) -> dict[str, str]:
    return repository.outlet_names(db, {sop.outlet_id for sop in sops if sop.outlet_id})


def media_file(db: Session, name: str) -> tuple[bytes, str]:
    stored = uploads.read(db, f"{MEDIA_FOLDER}/{name}") if "/" not in name and ".." not in name else None
    if stored is None:
        raise DomainError(messages.MEDIA_NOT_FOUND, status=NOT_FOUND)
    return stored


def reads(db: Session, user: User) -> list[SopRead]:
    return repository.reads_of(db, user.id)


def mark_read(db: Session, user: User, sop_id: str, version: int) -> SopRead:
    """Recorded when the last slide is finished; a version ahead of the procedure is refused."""
    sop = get_active(db, user, sop_id)
    if version > sop.version:
        raise DomainError(messages.VERSION_AHEAD, status=BAD_REQUEST)
    read = repository.record_read(db, sop.id, user.id, version, now())
    db.commit()
    return read
