"""The shape of promos and cafe announcements as the web and the tablet send and read them."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.core.catalog import promotions
from app.core.http import static_url
from app.models.cafe_promotion import CafePromotion
from app.models.promo import Promo

MAX_NAME_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 2000
MAX_LINK_LENGTH = 1000

PromoKind = Literal["basic", "produk", "total"]
DiscountType = Literal["persen", "nominal"]
Activation = Literal["otomatis", "manual"]
Status = Literal["berlaku", "terjadwal", "berakhir", "nonaktif"]


class PromoIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    # basic cuts the whole order, produk only the chosen menus, total only above a minimum spend.
    kind: PromoKind
    discount_type: DiscountType
    value: Decimal = Field(gt=0)
    product_ids: list[str] | None = None
    minimum_spend: Decimal | None = Field(None, gt=0)
    # otomatis applies by itself at the cashier; manual waits for the cashier to pick it.
    activation: Activation = "otomatis"
    starts_on: date
    ends_on: date
    is_active: bool = True
    # Kosong berlaku di semua cabang; dari tablet diabaikan, karena tablet hanya membuat untuk cabangnya sendiri.
    outlet_id: str | None = None


class PromoUpdateIn(BaseModel):
    """A field left out stays as it is."""

    name: str | None = Field(None, min_length=1, max_length=MAX_NAME_LENGTH)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    kind: PromoKind | None = None
    discount_type: DiscountType | None = None
    value: Decimal | None = Field(None, gt=0)
    product_ids: list[str] | None = None
    minimum_spend: Decimal | None = Field(None, gt=0)
    activation: Activation | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    is_active: bool | None = None
    outlet_id: str | None = None


class PromoOut(BaseModel):
    id: str
    name: str
    description: str | None
    kind: str
    discount_type: str
    value: Decimal
    product_ids: list[str]
    product_names: list[str]
    minimum_spend: Decimal | None
    activation: str
    starts_on: date
    ends_on: date
    is_active: bool
    # Kosong berlaku di semua cabang.
    outlet_id: str | None
    status: Status
    created_at: datetime


class AnnouncementIn(BaseModel):
    title: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    description: str = Field(min_length=1, max_length=MAX_DESCRIPTION_LENGTH)
    # A link from elsewhere; an uploaded picture goes through the image route instead.
    image_link: str | None = Field(None, max_length=MAX_LINK_LENGTH)
    starts_on: date
    ends_on: date
    is_active: bool = True
    outlet_id: str | None = None


class AnnouncementUpdateIn(BaseModel):
    """A field left out stays as it is; image_link sent empty removes the picture."""

    title: str | None = Field(None, min_length=1, max_length=MAX_NAME_LENGTH)
    description: str | None = Field(None, min_length=1, max_length=MAX_DESCRIPTION_LENGTH)
    image_link: str | None = Field(None, max_length=MAX_LINK_LENGTH)
    starts_on: date | None = None
    ends_on: date | None = None
    is_active: bool | None = None
    outlet_id: str | None = None


class AnnouncementOut(BaseModel):
    id: str
    title: str
    description: str
    image_url: str | None
    # True when the picture is a link pasted from elsewhere rather than an uploaded file.
    image_is_link: bool
    starts_on: date
    ends_on: date
    is_active: bool
    outlet_id: str | None
    status: Status
    created_at: datetime


class PromoMenuOut(BaseModel):
    id: str
    name: str


def promo_out(promo: Promo, menu_names: dict[str, str]) -> PromoOut:
    product_ids = promo.product_ids or []
    return PromoOut(
        id=promo.id,
        name=promo.name,
        description=promo.description,
        kind=promo.kind,
        discount_type=promo.discount_type,
        value=promo.value,
        product_ids=product_ids,
        # A menu removed since keeps its id here but has no name to show.
        product_names=[menu_names[menu_id] for menu_id in product_ids if menu_id in menu_names],
        minimum_spend=promo.minimum_spend,
        activation=promo.activation,
        starts_on=promo.starts_on,
        ends_on=promo.ends_on,
        is_active=promo.is_active,
        outlet_id=promo.outlet_id,
        status=promotions.status_of(promo.is_active, promo.starts_on, promo.ends_on),
        created_at=promo.created_at,
    )


def announcement_out(item: CafePromotion, base_url: str) -> AnnouncementOut:
    uploaded = promotions.uploaded_path(item.image)
    return AnnouncementOut(
        id=item.id,
        title=item.title,
        description=item.description,
        image_url=static_url(base_url, uploaded) if uploaded else item.image,
        image_is_link=bool(item.image) and uploaded is None,
        starts_on=item.starts_on,
        ends_on=item.ends_on,
        is_active=item.is_active,
        outlet_id=item.outlet_id,
        status=promotions.status_of(item.is_active, item.starts_on, item.ends_on),
        created_at=item.created_at,
    )


def promo_changes(body: PromoUpdateIn) -> dict:
    """A field sent empty on a required column keeps the saved value; only the optional ones can be cleared."""
    sent = {field: getattr(body, field) for field in body.model_fields_set}
    return {key: value for key, value in sent.items() if value is not None or key in ("description", "product_ids", "minimum_spend", "outlet_id")}


def announcement_changes(body: AnnouncementUpdateIn) -> dict:
    sent = {field: getattr(body, field) for field in body.model_fields_set}
    return {key: value for key, value in sent.items() if value is not None or key in ("image_link", "outlet_id")}
