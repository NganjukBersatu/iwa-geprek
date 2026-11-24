from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from web.management.payment_methods.constants import CODE_PATTERN, MAX_FEE_PERCENT, MAX_LABEL_LENGTH, MAX_NOTE_LENGTH


class PaymentMethodCreateIn(BaseModel):
    code: str = Field(pattern=CODE_PATTERN)
    label: str = Field(min_length=1, max_length=MAX_LABEL_LENGTH)
    icon: str
    needs_change: bool = False

    @field_validator("code", mode="before")
    @classmethod
    def _lower(cls, value):
        """Tidied before the pattern runs, so "GoPay" becomes the valid "gopay" instead of a raw pattern error."""
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("label", mode="before")
    @classmethod
    def _strip(cls, value):
        return value.strip() if isinstance(value, str) else value


class PaymentMethodUpdateIn(BaseModel):
    """The code is left out on purpose: past orders keep it, so changing it would cut them off from this method."""

    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(None, min_length=1, max_length=MAX_LABEL_LENGTH)
    icon: str | None = None
    position: int | None = Field(None, ge=0)
    is_active: bool | None = None
    needs_change: bool | None = None
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)
    fee_percent: Decimal | None = Field(None, ge=0, le=MAX_FEE_PERCENT)

    @field_validator("label", mode="before")
    @classmethod
    def _strip(cls, value):
        return value.strip() if isinstance(value, str) else value


class PaymentMethodOut(BaseModel):
    id: str
    outlet_id: str
    outlet_name: str
    code: str
    label: str
    icon: str
    position: int
    is_active: bool
    needs_change: bool
    note: str
    fee_percent: Decimal
    image_url: str | None
    # Orders that already used this method, so the delete prompt can say what it touches.
    used_by_orders: int
    missing: list[str]
