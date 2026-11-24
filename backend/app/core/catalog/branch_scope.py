"""Which branches a catalog item belongs to: no branch means every branch, one branch means that branch only."""
from sqlalchemy import cast, func, literal, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.errors import DomainError
from app.models.outlet import Outlet

BRANCH_UNKNOWN = "Cabang tidak ditemukan."
FORBIDDEN = 403


def checked(db: Session, outlet_id: str | None) -> str | None:
    """None keeps the item for every branch; an id must be a branch that exists."""
    if outlet_id is None:
        return None
    if db.scalar(select(Outlet.id).where(Outlet.id == outlet_id)) is None:
        raise DomainError(BRANCH_UNKNOWN)
    return outlet_id


def guard(owner_outlet_id: str | None, outlet_scope: str | None, not_found: str, elsewhere: str, not_found_status: int) -> None:
    """With a branch scope (a tablet) another branch's item is as good as absent, and one for every branch is read-only."""
    if outlet_scope is None:
        return
    if not offered_at(owner_outlet_id, outlet_scope):
        raise DomainError(not_found, status=not_found_status)
    if not owned_by(owner_outlet_id, outlet_scope):
        raise DomainError(elsewhere, status=FORBIDDEN)



def offered_at(owner_outlet_id: str | None, outlet_id: str) -> bool:
    return owner_outlet_id is None or owner_outlet_id == outlet_id


def owned_by(owner_outlet_id: str | None, outlet_id: str) -> bool:
    """A tablet changes only what belongs to its own branch; what applies to every branch is changed from the web."""
    return owner_outlet_id == outlet_id


def listed_at(outlet_ids: list[str] | None, outlet_id: str) -> bool:
    """The same for an item that lists its branches: no list means every branch."""
    return not outlet_ids or outlet_id in outlet_ids


def listed_only_at(outlet_ids: list[str] | None, outlet_id: str) -> bool:
    return outlet_ids == [outlet_id]


def listed_at_clause(column, outlet_id: str) -> ColumnElement[bool]:
    """The SQL twin of `listed_at` for a JSON list column: nothing stored, an empty list, or a list naming the branch."""
    listed = cast(column, JSONB)
    return or_(column.is_(None), func.jsonb_typeof(listed) != "array", listed == literal([], JSONB), listed.contains([outlet_id]))
