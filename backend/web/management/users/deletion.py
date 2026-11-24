"""Deleting an account: the row stays as the owner of its history, so no sale, session, expense, stock card or attendance changes."""
from sqlalchemy.orm import Session

from app.core.auth import end_all_sessions
from app.core.clock import now
from app.models.user import User


def delete_user(db: Session, user: User) -> None:
    """Does not commit; the account stops signing in at once and leaves every list, while reports keep reading its name."""
    user.deleted_at = now()
    user.is_active = False
    # Let go, so a role no one at work holds can still be deleted.
    user.role_id = None
    end_all_sessions(db, user.id)
