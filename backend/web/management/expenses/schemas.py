from datetime import date, datetime

from pydantic import BaseModel


class SessionChoiceOut(BaseModel):
    id: str
    outlet_id: str
    business_day: date
    cashier_username: str
    shift_code: str | None
    opened_at: datetime
    running: bool
    has_shopping_fund: bool


class SessionChoicePageOut(BaseModel):
    items: list[SessionChoiceOut]
    # Kosong berarti daftar sudah habis.
    next_cursor: str | None
