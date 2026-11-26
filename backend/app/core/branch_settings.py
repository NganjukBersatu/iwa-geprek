"""Baris pengaturan satu cabang (struk, harga dan margin, aturan absensi): satu pintu yang membuatnya bila belum ada."""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.orders import order_types
from app.models.cafe_settings import CafeSettings
from app.models.outlet import Outlet

DEFAULT_TOLERANCE_MINUTES = 5
DEFAULT_PENALTY_PER_MINUTE = 500
DEFAULT_AUTO_CLOSE_HOURS = 9
DEFAULT_MARKUP_PERCENT = Decimal(30)


def ensure(db: Session, outlet_id: str) -> CafeSettings:
    """Mengembalikan baris pengaturan cabang, membuatnya dengan nilai bawaan dan nama outlet sama dengan nama cabang bila belum ada."""
    row = db.get(CafeSettings, outlet_id)
    if row is not None:
        return row
    # Dikunci supaya dua simpan pertama yang bersamaan tidak sama-sama membuat baris.
    name = db.scalar(select(Outlet.name).where(Outlet.id == outlet_id).with_for_update()) or ""
    row = db.get(CafeSettings, outlet_id)
    if row is not None:
        return row
    row = CafeSettings(
        outlet_id=outlet_id,
        name=name,
        address="",
        phone="",
        complaint_number="",
        wifi=[],
        wifi_password="",
        social=[],
        receipt_greeting="",
        late_tolerance_minutes=DEFAULT_TOLERANCE_MINUTES,
        late_penalty_per_minute=DEFAULT_PENALTY_PER_MINUTE,
        auto_close_after_hours=DEFAULT_AUTO_CLOSE_HOURS,
        cost_markup_percent=DEFAULT_MARKUP_PERCENT,
        target_margin_percent=None,
        tax_percent=Decimal(0),
        service_percent=Decimal(0),
        default_order_type=order_types.DINE_IN,
    )
    db.add(row)
    db.flush()
    return row
