"""Kinerja karyawan untuk admin, dihitung dengan rumus yang sama persis dengan halaman Kinerja di app karyawan."""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.employee.performance import service as performance
from app.employee.performance.domain import Performance, Range
from app.models.user import User
from web.management.user_performance import messages, repository
from web.management.user_performance.constants import NOT_FOUND


@dataclass(frozen=True)
class Measured:
    user: User
    outlet_name: str | None
    performance: Performance


def everyone(db: Session, outlet_id: str | None, search: str | None, range_: Range, at: datetime) -> list[Measured]:
    people = repository.people(db, outlet_id, search)
    built = performance.build_many(db, people, range_, at)
    outlets = repository.outlet_names(db, {person.outlet_id for person in people if person.outlet_id})
    return [Measured(person, outlets.get(person.outlet_id) if person.outlet_id else None, built[person.id]) for person in people]


def one(db: Session, user_id: str, outlet_id: str | None, range_: Range, at: datetime) -> Measured:
    """Akun yang terikat satu cabang tidak bisa membedakan karyawan cabang lain dari yang tidak ada."""
    person = repository.person(db, user_id, outlet_id)
    if person is None:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    outlets = repository.outlet_names(db, {person.outlet_id} if person.outlet_id else set())
    return Measured(person, outlets.get(person.outlet_id) if person.outlet_id else None, performance.build(db, person, range_, at))
