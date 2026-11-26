"""The cafe identity printed on receipts and the pricing defaults of one branch."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import branch_settings
from app.core.errors import DomainError
from app.models.cafe_settings import CafeSettings
from app.models.outlet import Outlet
from web.management.cafe_settings import messages

NOT_FOUND = 404
INVALID = 422
PLAIN = ("name", "address", "phone", "complaint_number", "wifi_password", "receipt_greeting")
CHOICES = ("default_order_type",)
NUMBERS = ("cost_markup_percent", "target_margin_percent", "tax_percent", "service_percent")


def read(db: Session, outlet_id: str) -> CafeSettings | None:
    _ensure_outlet(db, outlet_id)
    return db.get(CafeSettings, outlet_id)


def update(db: Session, outlet_id: str, values: dict) -> CafeSettings:
    _ensure_outlet(db, outlet_id)
    if "name" in values and values["name"] is not None and not values["name"].strip():
        raise DomainError(messages.NAME_REQUIRED, status=INVALID)
    row = branch_settings.ensure(db, outlet_id)
    for field in PLAIN:
        if values.get(field) is not None:
            setattr(row, field, values[field].strip())
    for field in CHOICES:
        if values.get(field) is not None:
            setattr(row, field, values[field])
    if values.get("wifi") is not None:
        row.wifi = values["wifi"]
    if values.get("social") is not None:
        row.social = [{"ikon": entry["icon"], "handle": entry["handle"]} for entry in values["social"]]
    for field in NUMBERS:
        if field in values and (values[field] is not None or field == "target_margin_percent"):
            setattr(row, field, values[field])
    db.commit()
    return row


def _ensure_outlet(db: Session, outlet_id: str) -> None:
    if db.scalar(select(Outlet.id).where(Outlet.id == outlet_id)) is None:
        raise DomainError(messages.BRANCH_UNKNOWN, status=NOT_FOUND)
