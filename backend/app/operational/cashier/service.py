"""What the till shows: the branch's menu, best sellers, payment methods, promos, receipt header and ticket stations."""
from collections.abc import Callable
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.catalog import availability, selling
from app.core.catalog.selling import SellableMenu
from app.core.catalog.menu import CATEGORY_KIND
from app.core.finance.payment_methods import is_open, methods_of
from app.core.http import static_url
from app.core.orders import lines as line_rules
from app.models.cafe_settings import CafeSettings
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment_method import PaymentMethod
from app.models.promo import Promo
from app.operational.cashier.schemas import CashierMenuOut, ChoiceOut, ExtraOut, ShopOut, StationOut, VariantGroupOut
from app.operational.menu import repository as menu_repository


def _till_order(categories: dict[str, str]) -> Callable[[SellableMenu], tuple[bool, str, str, str]]:
    """Kategori sesuai abjad lalu nama menu, karena tablet menyusun tab kategorinya dari urutan menu ini; menu tanpa kategori di akhir."""

    def key(item: SellableMenu) -> tuple[bool, str, str, str]:
        category = categories.get(item.menu.category_id or "")
        return (category is None, (category or "").casefold(), item.menu.name.casefold(), item.menu.id)

    return key


def menu(db: Session, outlet_id: str, base_url: str) -> list[CashierMenuOut]:
    categories = {category.id: category.name for category in menu_repository.menu_categories(db)}
    sellable = sorted(selling.menus_of(db, outlet_id), key=_till_order(categories))
    ids = [item.menu.id for item in sellable]
    ready = line_rules.ready_ids(db, outlet_id, ids)
    missing = line_rules.missing_ingredients(db, outlet_id, ids)
    marked_out = availability.off_ids(db, outlet_id, ids)
    return [
        CashierMenuOut(
            id=item.menu.id,
            name=item.menu.name,
            price=item.price,
            category_id=item.menu.category_id,
            category_name=categories.get(item.menu.category_id or ""),
            image_url=static_url(base_url, item.menu.image_path),
            is_available=item.menu.is_available and item.menu.id not in marked_out,
            ready_to_sell=item.menu.id in ready,
            missing_ingredients=missing.get(item.menu.id, []),
            variant_groups=[
                VariantGroupOut(id=group.id, name=group.name, required=group.required, choices=[ChoiceOut(id=choice.id, name=choice.name) for choice in group.choices])
                for group in item.variant_groups
            ],
            extras=[ExtraOut(id=extra.id, name=extra.name, price=extra.price) for extra in item.extras],
        )
        for item in sellable
    ]


def best_seller_ids(db: Session, limit: int) -> list[str]:
    """Counted from the portions sold at every branch, as the legacy till did; a voided sale never happened, and a menu that is off cannot be offered."""
    sold = func.sum(OrderItem.qty)
    return list(
        db.scalars(
            select(MenuItem.id)
            .join(OrderItem, OrderItem.menu_item_id == MenuItem.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(MenuItem.is_available.is_(True), Order.voided_at.is_(None))
            .group_by(MenuItem.id, MenuItem.name)
            .order_by(sold.desc(), MenuItem.name)
            .limit(limit)
        ).all()
    )


def methods(db: Session, outlet_id: str, with_unready: bool = False) -> list[PaymentMethod]:
    """Switched-on methods; those not yet fully set up only when asked, so the till can show them as unavailable."""
    return [method for method in methods_of(db, outlet_id) if (method.is_active if with_unready else is_open(method))]


def promos(db: Session, day: date, outlet_id: str) -> list[Promo]:
    """Not ended by `day`, the business day the till works in, for every branch or this one; ordered by when they were made, so two promos on one menu always resolve to the same one on every till."""
    return list(
        db.scalars(
            select(Promo)
            .where(Promo.is_active.is_(True), Promo.ends_on >= day, or_(Promo.outlet_id.is_(None), Promo.outlet_id == outlet_id))
            .order_by(Promo.created_at, Promo.id)
        ).all()
    )


def shop(db: Session, outlet_id: str) -> ShopOut:
    settings = db.get(CafeSettings, outlet_id)
    if settings is None:
        return ShopOut(name="", address="", phone="", receipt_greeting="")
    return ShopOut(
        name=settings.name,
        address=settings.address,
        phone=settings.phone,
        receipt_greeting=settings.receipt_greeting,
        has_wifi=bool(settings.wifi),
        wifi_password=settings.wifi_password or "",
        complaint_number=settings.complaint_number or "",
        # Every entry, even one without a handle, so the receipt matches the web till's line for line.
        social_handles=[str(entry.get("handle", "")) for entry in settings.social or [] if isinstance(entry, dict)],
        default_order_type=settings.default_order_type,
    )


def stations(db: Session) -> list[StationOut]:
    rows = db.scalars(select(Category).where(Category.kind == CATEGORY_KIND, Category.station.is_not(None)).order_by(Category.name)).all()
    return [StationOut(category_name=category.name, station=category.station or "") for category in rows]
