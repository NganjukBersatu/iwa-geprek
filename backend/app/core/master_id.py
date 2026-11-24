"""The shared id above lists kept per branch (payment methods, shift codes, visitor kinds), so the "same" row matches across branches by id, not text."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session


def tidy(text: str) -> str:
    return " ".join(text.split())


def for_new_row(db: Session, model, column, value: str, outlet_id: str) -> str:
    """Reuses the master id of a matching row at another branch, unless this branch already uses it; does not commit."""
    key = tidy(value).lower()
    used_here = select(model.master_id).where(model.outlet_id == outlet_id, model.master_id.is_not(None))
    existing = db.scalar(
        select(model.master_id)
        .where(
            func.lower(column) == key,
            model.outlet_id != outlet_id,
            model.master_id.is_not(None),
            model.master_id.not_in(used_here),
        )
        .limit(1)
    )
    return existing or str(uuid.uuid4())
