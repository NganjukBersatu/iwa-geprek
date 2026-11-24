"""Official receipt numbers, "{branch code}/{branch number}/{YYMMDD}/{sequence}".

Taken once at the start of a sale, before payment, so the kitchen ticket printed first and the receipt after it carry the same number.
"""
from datetime import date

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.outlet import Outlet
from app.models.receipt_counter import ReceiptCounter

DAY_FORMAT = "%y%m%d"
SEQUENCE_DIGITS = 4


def take(db: Session, outlet_id: str, day: date) -> str:
    """`day` is the business day of the session ringing the sale, so one session never carries two days of numbers; raises that day's sequence atomically and commits on its own."""
    outlet = db.get(Outlet, outlet_id)
    statement = (
        insert(ReceiptCounter)
        .values(outlet_id=outlet_id, day=day, sequence=1)
        .on_conflict_do_update(index_elements=["outlet_id", "day"], set_={"sequence": ReceiptCounter.sequence + 1})
        .returning(ReceiptCounter.sequence)
    )
    sequence = db.execute(statement).scalar_one()
    # A number already taken must not come back if a later step of the sale fails.
    db.commit()
    parts = [outlet.code if outlet else None, outlet.receipt_number if outlet else None, day.strftime(DAY_FORMAT), f"{sequence:0{SEQUENCE_DIGITS}d}"]
    return "/".join(part for part in parts if part)
