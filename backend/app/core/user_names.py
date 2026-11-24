"""Display names of user, for any screen that names who did something."""
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def user_names(db: Session, user_ids: Iterable[str | None]) -> dict[str, str]:
    """In one query; the username stands in for a missing name."""
    wanted = {user_id for user_id in user_ids if user_id}
    if not wanted:
        return {}
    rows = db.execute(select(User.id, User.name, User.username).where(User.id.in_(wanted))).all()
    return {user_id: name or username for user_id, name, username in rows}
