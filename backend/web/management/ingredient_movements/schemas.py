from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from web.management.ingredient_movements import constants as c

# "use" adalah pemakaian manual bahan tidak langsung: kartu keluar tanpa pesanan.
Kind = Literal["masuk", "keluar", "rusak", "rnd", "penyesuaian", "use"]


class ReceiptIn(BaseModel):
    """Ingredients that arrived: the stock goes up and nothing else; money is recorded on the expense screen."""

    ingredient_id: str
    qty: Decimal = Field(gt=0, description="In the unit of the ingredient, e.g. 800 for 800 g")
    note: str | None = Field(None, max_length=c.MAX_NOTE_LENGTH)


class WasteIn(BaseModel):
    """Ingredient thrown away; the quantity is positive and the server stores it as a decrease."""

    ingredient_id: str
    qty: Decimal = Field(gt=0)
    cause: str = Field(min_length=1, max_length=30, description="A code from the causes list; without it, natural shrinkage cannot be told from carelessness")
    note: str | None = Field(None, max_length=c.MAX_NOTE_LENGTH)


class UseIn(BaseModel):
    """Daily use of an indirect ingredient; the quantity is positive and the server stores it as a decrease."""

    ingredient_id: str
    qty: Decimal = Field(gt=0)
    cause: str = Field(min_length=1, max_length=30, description="A code from the usage causes list")
    note: str | None = Field(None, max_length=c.MAX_NOTE_LENGTH)
    client_id: str | None = Field(None, min_length=8, max_length=64, description="Random key; a resend with the same key returns the first card")


class TrialIn(BaseModel):
    """Ingredient used to try a new menu: it leaves, but it is neither a sale nor waste."""

    ingredient_id: str
    qty: Decimal = Field(gt=0)
    note: str = Field(min_length=1, max_length=c.MAX_NOTE_LENGTH, description="Which menu is being tried; the only trace of where the ingredient went")


class AdjustmentIn(BaseModel):
    """A manual correction of the balance; the reason is required, so every correction leaves a trace."""

    ingredient_id: str
    qty: Decimal = Field(description="Signed: positive adds, negative removes")
    note: str = Field(min_length=1, max_length=c.MAX_NOTE_LENGTH)


class CauseOut(BaseModel):
    code: str
    label: str
    human_error: bool


class MovementUpdateIn(BaseModel):
    """A field left out stays as it was; the direction of a movement never flips."""

    qty: Decimal | None = None
    note: str | None = Field(None, max_length=c.MAX_NOTE_LENGTH)


class MovementOut(BaseModel):
    id: str
    outlet_id: str
    business_day: date
    ingredient_id: str | None
    ingredient_name: str
    kind: str
    unit: str = Field(description="The unit of the ingredient, empty once the ingredient is gone")
    qty: Decimal = Field(description="Signed as on the ledger: arrivals positive, usage and waste negative")
    cause: str | None
    cause_label: str | None
    human_error: bool | None = Field(description="Only for waste: carelessness (true) against natural loss (false)")
    proof_url: str | None
    order_id: str | None
    count_id: str | None
    note: str | None
    user_id: str | None
    user_name: str | None
    created_at: datetime


class MovementPageOut(BaseModel):
    start: date
    end: date
    items: list[MovementOut]
    total: int = Field(description="Every row that matches the filters, not only this page")
    human_error_count: int = Field(description="Waste rows caused by carelessness, over every matching row")
    natural_count: int = Field(description="Waste rows caused by something natural, over every matching row")
    page: int
    size: int
