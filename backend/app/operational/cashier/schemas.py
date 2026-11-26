from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ChoiceOut(BaseModel):
    id: str
    name: str


class VariantGroupOut(BaseModel):
    id: str
    name: str
    required: bool
    choices: list[ChoiceOut]


class ExtraOut(BaseModel):
    id: str
    name: str
    price: Decimal


class CashierMenuOut(BaseModel):
    id: str
    name: str
    # The branch price, the same one the server charges.
    price: Decimal
    category_id: str | None
    category_name: str | None
    image_url: str | None
    is_available: bool
    ready_to_sell: bool
    missing_ingredients: list[str]
    variant_groups: list[VariantGroupOut]
    extras: list[ExtraOut]


class CashierMethodOut(BaseModel):
    code: str
    label: str
    needs_change: bool
    # A Tabler icon name ("ti-qrcode"); the till draws its own copy of that icon.
    icon: str = ""
    # What still has to be set up on the web before the cashier may use it ("gambar", "catatan"); empty when ready.
    missing: list[str] = []
    # The code or account the customer pays to, shown on the screen turned towards them.
    image_url: str | None = None
    note: str = ""


class CashierPromoOut(BaseModel):
    """Everything the till needs to work out the same discount as the server, also while offline."""

    id: str
    name: str
    kind: str
    discount_type: str
    value: Decimal
    product_ids: list[str]
    minimum_spend: Decimal | None
    activation: str
    starts_on: date
    ends_on: date


class ShopOut(BaseModel):
    """The receipt header of the branch."""

    name: str
    address: str
    phone: str
    receipt_greeting: str
    # The footer of the receipt, printed the same as the web till's.
    has_wifi: bool = False
    wifi_password: str = ""
    complaint_number: str = ""
    social_handles: list[str] = []
    # Jenis pesanan yang dipilih saat pesanan baru dimulai di kasir.
    default_order_type: str = "free_table"


class StationOut(BaseModel):
    """Which ticket printer a menu category goes to: bar, kitchen or cashier."""

    category_name: str
    station: str


class VisitorKindOut(BaseModel):
    id: str
    name: str
    # The cashier then also picks the gender of whoever orders.
    asks_gender: bool


class VisitorGenderOut(BaseModel):
    id: str
    name: str


class VisitorChoicesOut(BaseModel):
    """Only the active choices of the branch; both may be empty, since recording visitors is optional."""

    categories: list[VisitorKindOut]
    genders: list[VisitorGenderOut]
