# Satu pintu harga jual menu per cabang, supaya setiap layar menampilkan harga yang ditagih kasir.
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.money import ZERO, decimal_of, round_rupiah
from app.models.cafe_settings import CafeSettings
from app.models.menu_item import MenuItem, MenuOutletPrice

PERCENT = 100


def final_price(price: Decimal, tax_percent: Decimal, service_percent: Decimal) -> Decimal:
    total_percent = tax_percent + service_percent
    if total_percent == 0:
        return price
    return round_rupiah(price * (1 + total_percent / PERCENT))


def _with_tax_and_service(menu: MenuItem, price: Decimal, settings: CafeSettings | None) -> Decimal:
    # Cabang tanpa baris pengaturan berarti pajak dan layanan 0%; persentase milik menu mengalahkan milik cabang.
    default_tax = Decimal(str(settings.tax_percent)) if settings else ZERO
    default_service = Decimal(str(settings.service_percent)) if settings else ZERO
    tax = Decimal(str(menu.tax_percent)) if menu.tax_percent is not None else default_tax
    service = Decimal(str(menu.service_percent)) if menu.service_percent is not None else default_service
    return final_price(price, tax, service)


def price_map_many(db: Session, outlet_ids: list[str], menus: list[MenuItem], settings: dict[str, CafeSettings]) -> dict[tuple[str, str], Decimal]:
    # Satu query berapa pun jumlah cabangnya.
    base = {(outlet_id, menu.id): decimal_of(menu.price) for outlet_id in outlet_ids for menu in menus}
    if base:
        rows = db.execute(
            select(MenuOutletPrice.outlet_id, MenuOutletPrice.menu_item_id, MenuOutletPrice.price).where(
                MenuOutletPrice.outlet_id.in_(outlet_ids), MenuOutletPrice.menu_item_id.in_([menu.id for menu in menus])
            )
        ).all()
        for outlet_id, menu_id, price in rows:
            base[(outlet_id, menu_id)] = Decimal(str(price))
    return {(outlet_id, menu.id): _with_tax_and_service(menu, base[(outlet_id, menu.id)], settings.get(outlet_id)) for outlet_id in outlet_ids for menu in menus}


def price_map(db: Session, outlet_id: str | None, menus: list[MenuItem]) -> dict[str, Decimal]:
    # Tanpa cabang, harga dasar dikembalikan apa adanya.
    result = {menu.id: decimal_of(menu.price) for menu in menus}
    if not outlet_id or not menus:
        return result
    rows = db.execute(
        select(MenuOutletPrice.menu_item_id, MenuOutletPrice.price).where(
            MenuOutletPrice.outlet_id == outlet_id,
            MenuOutletPrice.menu_item_id.in_(list(result)),
        )
    ).all()
    for menu_id, price in rows:
        result[menu_id] = Decimal(str(price))

    settings = db.get(CafeSettings, outlet_id)
    for menu in menus:
        result[menu.id] = _with_tax_and_service(menu, result[menu.id], settings)
    return result
