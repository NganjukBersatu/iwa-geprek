"""Database reads for the user screen."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.search import contains
from app.models.outlet import Outlet
from app.models.role import Role
from app.models.user import User
from app.core.sorting import SqlSorting


SEARCHED = (
    User.name,
    User.username,
    User.phone,
    User.email,
    User.address,
    User.emergency_name,
    User.emergency_phone,
    User.emergency_relation,
)


SORTING = SqlSorting(
    columns={
        "name": func.coalesce(func.nullif(User.name, ""), User.username),
        "role": select(Role.name).where(Role.id == User.role_id).scalar_subquery(),
        "outlet": select(Outlet.name).where(Outlet.id == User.outlet_id).scalar_subquery(),
        "active": User.is_active,
    },
    # Inactive accounts sink to the bottom: the list manages people at work, not an archive.
    default=(User.is_active.desc(), User.username),
    tiebreak=User.id,
)


def page_of(
    db: Session, search: str | None, role_id: str | None, outlet_id: str | None, active: bool | None, sort: str | None, page: int, size: int
) -> tuple[list[User], int]:
    filters = [User.deleted_at.is_(None)]
    if search:
        # Every detail an account shows or keeps, except the password; role and branch are matched by their names.
        filters.append(
            or_(
                *(contains(column, search) for column in SEARCHED),
                User.role_id.in_(select(Role.id).where(contains(Role.name, search))),
                User.outlet_id.in_(select(Outlet.id).where(contains(Outlet.name, search))),
            )
        )
    if role_id:
        filters.append(User.role_id == role_id)
    if outlet_id:
        filters.append(User.outlet_id == outlet_id)
    if active is not None:
        filters.append(User.is_active.is_(active))
    total = db.scalar(select(func.count()).select_from(User).where(*filters)) or 0
    rows = db.scalars(
        select(User)
        .where(*filters)
        .order_by(*SORTING.order_by(sort))
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return list(rows), total


def find(db: Session, user_id: str) -> User | None:
    """A deleted account is gone for this screen; only reports still read its name."""
    user = db.get(User, user_id)
    return user if user is not None and user.deleted_at is None else None


def find_role(db: Session, role_id: str) -> Role | None:
    return db.get(Role, role_id)


def outlet_exists(db: Session, outlet_id: str) -> bool:
    return db.get(Outlet, outlet_id) is not None


def username_owner(db: Session, username: str) -> User | None:
    """Deleted accounts included: their username stays taken, so a report never shows two people under one name."""
    return db.scalar(select(User).where(func.lower(User.username) == username.lower()))
