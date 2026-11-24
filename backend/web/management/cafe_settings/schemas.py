from decimal import Decimal

from pydantic import BaseModel, Field

from web.management.cafe_settings import constants as c


class WifiEntry(BaseModel):
    area: str = Field(min_length=1, max_length=c.MAX_WIFI_TEXT)
    ssid: str = Field(min_length=1, max_length=c.MAX_WIFI_TEXT)


class SocialEntry(BaseModel):
    icon: str = Field(min_length=1, max_length=c.MAX_SOCIAL_TEXT, description="Tabler icon class, e.g. ti-brand-instagram")
    handle: str = Field(min_length=1, max_length=c.MAX_SOCIAL_TEXT)


class CafeSettingsIn(BaseModel):
    """A field left out stays as it was; an explicit null clears only the target margin."""

    name: str | None = Field(None, min_length=1, max_length=c.MAX_NAME)
    address: str | None = Field(None, max_length=c.MAX_ADDRESS)
    phone: str | None = Field(None, max_length=c.MAX_PHONE)
    complaint_number: str | None = Field(None, max_length=c.MAX_PHONE)
    wifi: list[WifiEntry] | None = Field(None, max_length=c.MAX_WIFI_ENTRIES)
    wifi_password: str | None = Field(None, max_length=c.MAX_WIFI_PASSWORD)
    social: list[SocialEntry] | None = Field(None, max_length=c.MAX_SOCIAL_ENTRIES)
    receipt_greeting: str | None = Field(None, max_length=c.MAX_GREETING)
    cost_markup_percent: Decimal | None = Field(None, ge=0, le=c.MAX_MARKUP_PERCENT)
    target_margin_percent: Decimal | None = Field(None, gt=0, lt=c.MAX_PERCENT)
    tax_percent: Decimal | None = Field(None, ge=0, le=c.MAX_PERCENT)
    service_percent: Decimal | None = Field(None, ge=0, le=c.MAX_PERCENT)


class CafeSettingsOut(BaseModel):
    outlet_id: str
    exists: bool = Field(description="False while the branch has no settings row yet")
    name: str
    address: str
    phone: str
    complaint_number: str
    wifi: list[WifiEntry]
    wifi_password: str
    social: list[SocialEntry]
    receipt_greeting: str
    cost_markup_percent: Decimal
    target_margin_percent: Decimal | None
    tax_percent: Decimal
    service_percent: Decimal
