"""The one door for which payment methods a branch has and whether each is ready to take money."""
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import master_id
from app.core.branches import branch_ids_in_scope
from app.core.errors import DomainError
from app.models.order import CASH_METHOD
from app.models.outlet import Outlet
from app.models.payment_method import PaymentMethod

NOT_FOUND = 404
BRANCH_NOT_FOUND = "Cabang tidak ditemukan."

REQUIREMENT_IMAGE = "gambar"
REQUIREMENT_NOTE = "catatan"

# A short fixed list: a mistyped icon name raises no error, it only leaves an empty button on the cashier screen.
ICONS = (
    "ti-cash",
    "ti-qrcode",
    "ti-credit-card",
    "ti-building-bank",
    "ti-device-mobile",
    "ti-wallet",
    "ti-receipt",
    "ti-gift",
)

# A new branch starts from these, never from another branch: its QRIS and account numbers must not travel.
DEFAULT_METHODS = (
    {"code": CASH_METHOD, "label": "Tunai", "icon": "ti-cash", "needs_change": True},
    {"code": "qris", "label": "QRIS", "icon": "ti-qrcode", "needs_change": True},
    {"code": "debit", "label": "Kartu Debit/Kredit", "icon": "ti-credit-card", "needs_change": False},
    {"code": "transfer", "label": "Transfer Bank", "icon": "ti-building-bank", "needs_change": False},
)


def missing_requirements(method: PaymentMethod) -> list[str]:
    """Cash needs nothing; every other method needs an uploaded image and a note before the cashier may use it."""
    if method.code == CASH_METHOD:
        return []
    missing = []
    if not method.image_path:
        missing.append(REQUIREMENT_IMAGE)
    if not (method.note or "").strip():
        missing.append(REQUIREMENT_NOTE)
    return missing


def is_open(method: PaymentMethod) -> bool:
    """Switched on and fully set up: the till can take money with it."""
    return method.is_active and not missing_requirements(method)


def open_non_cash_labels(db: Session, outlet_ids: list[str]) -> list[str]:
    """Labels of the non-cash methods open in any of these branches, each label once, in till order; one query."""
    if not outlet_ids:
        return []
    found = db.scalars(
        select(PaymentMethod)
        .where(PaymentMethod.outlet_id.in_(outlet_ids), PaymentMethod.code != CASH_METHOD, PaymentMethod.is_active.is_(True))
        .order_by(PaymentMethod.position, PaymentMethod.label)
    ).all()
    return list(dict.fromkeys(method.label for method in found if is_open(method)))


def _of_branch(db: Session, outlet_id: str) -> list[PaymentMethod]:
    return list(
        db.scalars(
            select(PaymentMethod)
            .where(PaymentMethod.outlet_id == outlet_id)
            .order_by(PaymentMethod.position, PaymentMethod.label)
        ).all()
    )


def methods_of_all(db: Session) -> list[PaymentMethod]:
    """Every active branch's methods, branch by branch, read in one query."""
    outlet_ids = branch_ids_in_scope(db, None)
    if not outlet_ids:
        return []
    found = list(
        db.scalars(
            select(PaymentMethod).where(PaymentMethod.outlet_id.in_(outlet_ids)).order_by(PaymentMethod.position, PaymentMethod.label)
        ).all()
    )
    by_branch: dict[str, list[PaymentMethod]] = {outlet_id: [] for outlet_id in outlet_ids}
    for method in found:
        by_branch[method.outlet_id].append(method)
    return [method for outlet_id in outlet_ids for method in by_branch[outlet_id]]


def methods_of(db: Session, outlet_id: str) -> list[PaymentMethod]:
    """Only reads. A branch gets its methods when it is made (seed_defaults); one that has none is reported as such, never filled in here."""
    methods = _of_branch(db, outlet_id)
    if not methods and db.get(Outlet, outlet_id) is None:
        raise DomainError(BRANCH_NOT_FOUND, status=NOT_FOUND)
    return methods


def seed_defaults(db: Session, outlet_id: str) -> None:
    """The methods every new branch starts with, since an empty list makes every payment fail for no visible reason; the caller commits."""
    for position, default in enumerate(DEFAULT_METHODS):
        db.add(
            PaymentMethod(
                id=str(uuid.uuid4()),
                outlet_id=outlet_id,
                master_id=master_id.for_new_row(db, PaymentMethod, PaymentMethod.code, default["code"], outlet_id),
                code=default["code"],
                label=default["label"],
                icon=default["icon"],
                position=position,
                is_active=True,
                needs_change=default["needs_change"],
                image_path=None,
                note="",
                fee_percent=Decimal("0"),
            )
        )
    db.flush()
