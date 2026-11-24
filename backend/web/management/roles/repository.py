"""Database reads for roles."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user import User
from app.models.station import Station


def all_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.sort_order, Role.name)).all())


def find(db: Session, role_id: str) -> Role | None:
    return db.get(Role, role_id)


def name_taken(db: Session, name: str, except_id: str | None = None) -> bool:
    statement = select(Role.id).where(func.lower(Role.name) == name.lower())
    if except_id is not None:
        statement = statement.where(Role.id != except_id)
    return db.scalar(statement) is not None


def stations(db: Session) -> list[tuple[str, str]]:
    return [(row.id, row.name) for row in db.execute(select(Station.id, Station.name).order_by(Station.position, Station.name, Station.id))]


def station_exists(db: Session, station_id: str) -> bool:
    return db.get(Station, station_id) is not None


def user_count(db: Session, role_id: str) -> int:
    return db.scalar(select(func.count()).select_from(User).where(User.role_id == role_id)) or 0
