from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.core.finance.session_rows import SessionHistoryRowOut
from app.core.orders.order_schemas import SessionOrderOut


class SessionCorrectionIn(BaseModel):
    """A field left out stays as it is; derived figures are worked out again, never typed."""

    opening_cash: Decimal | None = Field(None, ge=0)
    # Only for a closed session that was not opened with the three money parts.
    actual_cash: Decimal | None = Field(None, ge=0)
    note: str | None = Field(None, max_length=500)


class SessionInterventionIn(BaseModel):
    """An intervention on someone else's running session: the counted money and, always, the reason."""

    actual_cash: Decimal | None = Field(None, ge=0)
    actual_float: Decimal | None = Field(None, ge=0)
    actual_shopping: Decimal | None = Field(None, ge=0)
    actual_revenue: Decimal | None = Field(None, ge=0)
    note: str = Field(min_length=3, max_length=500)


class SessionClosingOut(BaseModel):
    """What the closing dialog shows before counting; three-part sessions ask for each part against its plan."""

    three_parts: bool
    expected_cash: Decimal
    planned_float: Decimal | None
    planned_shopping: Decimal | None
    expected_revenue: Decimal


OrderType = Literal["free_table", "take_away"]


class CorrectionExtraPickIn(BaseModel):
    """An extra chosen on a line; qty is per single portion of the menu item."""

    extra_id: str
    qty: int = Field(1, ge=1, le=99)


class CorrectionOrderLineIn(BaseModel):
    menu_item_id: str
    qty: int = Field(ge=1)
    note: str | None = Field(None, max_length=255)
    variant_ids: list[str] = Field(default_factory=list, max_length=20)
    extras: list[CorrectionExtraPickIn] = Field(default_factory=list, max_length=30)


class OrderVoidIn(BaseModel):
    reason: str = Field(min_length=3, max_length=255)


class OrderEditIn(BaseModel):
    """What is not sent is not changed; `lines` replaces every line of the order."""

    customer_name: str | None = Field(None, max_length=255)
    table_no: str | None = Field(None, max_length=32)
    order_type: OrderType | None = None
    payment_method: str | None = Field(None, max_length=16)
    cash_received: Decimal | None = Field(None, ge=0)
    lines: list[CorrectionOrderLineIn] | None = Field(None, min_length=1)
    promo_id: str | None = None
    # null cannot tell "unchanged" from "removed", so removing the promo is its own flag.
    remove_promo: bool = False


class SessionImpactOut(BaseModel):
    orders: int
    expenses: int


class CatalogChoiceOut(BaseModel):
    id: str
    name: str


class CatalogVariantGroupOut(BaseModel):
    id: str
    name: str
    required: bool
    choices: list[CatalogChoiceOut]


class CatalogExtraOut(BaseModel):
    id: str
    name: str
    price: Decimal


class CatalogMenuOut(BaseModel):
    id: str
    name: str
    price: Decimal
    variant_groups: list[CatalogVariantGroupOut]
    extras: list[CatalogExtraOut]


class CatalogPromoOut(BaseModel):
    id: str
    name: str
    # "ended" and "deleted" only appear for the promo the order already uses; a deleted one has no name left, so name is empty.
    status: Literal["active", "ended", "deleted"]


class CatalogMethodOut(BaseModel):
    code: str
    label: str
    needs_change: bool
    # "inactive" only appears for the method the order already uses, switched off or deleted since.
    status: Literal["active", "inactive"]


class OrderCatalogOut(BaseModel):
    """What the correction dialog may choose from, at the branch of the order."""

    menus: list[CatalogMenuOut]
    promos: list[CatalogPromoOut]
    methods: list[CatalogMethodOut]


class SessionHistoryPageOut(BaseModel):
    start: date
    end: date
    items: list[SessionHistoryRowOut]
    total: int
    page: int
    size: int


class SessionOrderDetailOut(SessionOrderOut):
    """One transaction with the session it belongs to, for the page of a single transaction."""

    cashier_username: str | None
