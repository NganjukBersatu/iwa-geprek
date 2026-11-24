"""Reading and changing the signed-in employee's own account."""
import uuid

from sqlalchemy.orm import Session

from app.core import branches, text_rules, uploads
from app.core.auth import end_all_sessions
from app.core.errors import DomainError
from app.core.messages import NAME_CHARACTERS
from app.core.password_policy import ensure_acceptable
from app.core.security import hash_password, verify_password
from app.core.uploads import UploadedFile
from app.employee.profile import messages
from app.employee.profile.constants import PHOTO_FOLDER
from app.employee.profile.domain import Profile
from app.employee.profile.upload import RULE
from app.models.user import User

# The fields the employee may change, by the name the request uses and the attribute they land on.
EDITABLE = {
    "name": "name",
    "phone": "phone",
    "address": "address",
    "birth_date": "birth_date",
    "gender": "gender",
    "email": "email",
    "emergency_name": "emergency_name",
    "emergency_phone": "emergency_phone",
    "emergency_relation": "emergency_relation",
}


def get_profile(db: Session, user: User) -> Profile:
    return Profile(user=user, outlet_name=branches.outlet_name(db, user.outlet_id))


def update_profile(db: Session, user: User, changes: dict) -> Profile:
    """The username, role, and branch are never changed here; those belong to the admin."""
    if "name" in changes and changes["name"] is None:
        raise DomainError(messages.NAME_REQUIRED, field="name")
    new_name = changes.get("name")
    if new_name is not None and new_name.strip() != (user.name or "") and not text_rules.is_plain_name(new_name.strip()):
        raise DomainError(NAME_CHARACTERS, field="name")
    for field, value in changes.items():
        setattr(user, EDITABLE[field], value)
    db.commit()
    db.refresh(user)
    return get_profile(db, user)


def change_password(db: Session, user: User, current_password: str, new_password: str, current_session: str) -> None:
    """Every other device signed in as the employee is signed out."""
    if not verify_password(current_password, user.password_hash):
        raise DomainError(messages.WRONG_PASSWORD, field="current_password")
    if new_password == current_password:
        raise DomainError(messages.SAME_PASSWORD, field="new_password")
    ensure_acceptable(new_password, user.username, field="new_password")
    user.password_hash = hash_password(new_password)
    end_all_sessions(db, user.id, keep=current_session)
    db.commit()


def set_photo(db: Session, user: User, image: UploadedFile) -> Profile:
    path = f"{PHOTO_FOLDER}/{user.id}/{uuid.uuid4()}{image.extension}"
    uploads.store(db, path, image, RULE)
    previous = user.photo_key
    user.photo_key = path
    db.commit()
    db.refresh(user)
    uploads.discard(db, previous)
    return get_profile(db, user)


def remove_photo(db: Session, user: User) -> None:
    previous = user.photo_key
    user.photo_key = None
    db.commit()
    uploads.discard(db, previous)
