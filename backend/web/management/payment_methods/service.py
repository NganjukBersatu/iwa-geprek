"""Managing a branch's payment methods; readiness and defaults come from app.core.finance."""
import uuid
from decimal import Decimal

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core import master_id, uploads
from app.core.errors import DomainError
from app.core.finance.payment_methods import ICONS, methods_of, methods_of_all
from app.core.uploads import UploadedFile
from app.models.order import Order
from app.models.payment_method import PaymentMethod
from web.management.payment_methods import messages, repository
from web.management.payment_methods.constants import IMAGE_FOLDER
from web.management.payment_methods.upload import RULE

NOT_FOUND = 404
CONFLICT = 409


def _checked_icon(icon: str) -> str:
    if icon not in ICONS:
        raise DomainError(messages.ICON_UNKNOWN)
    return icon


def _own(db: Session, outlet_id: str, method_id: str) -> PaymentMethod:
    method = repository.find(db, method_id)
    if method is None or method.outlet_id != outlet_id:
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return method


def list_methods(db: Session, outlet_id: str | None) -> tuple[list[PaymentMethod], dict[tuple[str, str], int]]:
    """Inactive ones included, so they can be switched back on; the cashier screen shows only the active ones. No branch means every branch."""
    methods = methods_of_all(db) if outlet_id is None else methods_of(db, outlet_id)
    return methods, repository.usage(db, outlet_id)


def get(db: Session, outlet_id: str | None, method_id: str) -> PaymentMethod:
    """One method for its page; a method of another branch answers as missing for someone bound to one branch."""
    method = repository.find(db, method_id)
    if method is None or (outlet_id and method.outlet_id != outlet_id):
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return method


def usage_of(db: Session, outlet_id: str, method: PaymentMethod) -> int:
    return repository.usage(db, outlet_id).get((outlet_id, method.code), 0)


def create(db: Session, outlet_id: str, code: str, label: str, icon: str, needs_change: bool) -> PaymentMethod:
    existing = methods_of(db, outlet_id)
    clash = repository.with_code(db, outlet_id, code)
    if clash is not None:
        raise DomainError(messages.CODE_TAKEN.format(code=code, label=clash.label), status=CONFLICT)
    method = PaymentMethod(
        id=str(uuid.uuid4()),
        outlet_id=outlet_id,
        master_id=master_id.for_new_row(db, PaymentMethod, PaymentMethod.code, code, outlet_id),
        code=code,
        label=label,
        icon=_checked_icon(icon),
        position=len(existing),
        is_active=True,
        needs_change=needs_change,
        image_path=None,
        note="",
        fee_percent=Decimal("0"),
    )
    db.add(method)
    db.commit()
    db.refresh(method)
    return method


def update(db: Session, outlet_id: str, method_id: str, changes: dict) -> PaymentMethod:
    method = _own(db, outlet_id, method_id)
    if "icon" in changes and changes["icon"] is not None:
        changes["icon"] = _checked_icon(changes["icon"])
    for field, value in changes.items():
        if value is not None:
            setattr(method, field, value)
    db.commit()
    db.refresh(method)
    return method


def delete(db: Session, outlet_id: str, method_id: str) -> None:
    """A method no order has used is deleted for real; one that was used is only switched off, so every order keeps its link. The last active method is always kept."""
    method = _own(db, outlet_id, method_id)
    if method.is_active and repository.other_active_count(db, outlet_id, method_id) == 0:
        raise DomainError(messages.LAST_ACTIVE, status=CONFLICT)
    if db.scalar(select(exists().where(Order.payment_method_id == method.id))):
        raise DomainError(messages.IN_USE, status=CONFLICT)
    image = method.image_path
    db.delete(method)
    db.commit()
    uploads.discard(db, image)


def set_image(db: Session, outlet_id: str, method_id: str, image: UploadedFile) -> PaymentMethod:
    method = _own(db, outlet_id, method_id)
    path = f"{IMAGE_FOLDER}/{method.id}/{uuid.uuid4()}{image.extension}"
    uploads.store(db, path, image, RULE)
    previous = method.image_path
    method.image_path = path
    db.commit()
    db.refresh(method)
    uploads.discard(db, previous)
    return method


def remove_image(db: Session, outlet_id: str, method_id: str) -> PaymentMethod:
    method = _own(db, outlet_id, method_id)
    previous = method.image_path
    method.image_path = None
    db.commit()
    db.refresh(method)
    uploads.discard(db, previous)
    return method
