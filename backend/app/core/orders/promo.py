# Potongan promo untuk satu order; layar kasir dan total yang tersimpan tidak boleh berbeda.
from datetime import date
from decimal import Decimal

from sqlalchemy import ColumnElement

from app.core import clock
from app.core.money import ZERO, round_rupiah
from app.models.promo import Promo

KIND_BASIC = "basic"
KIND_TOTAL = "total"
KIND_PRODUCT = "produk"
TYPE_PERCENT = "persen"
TYPE_NOMINAL = "nominal"
PERCENT = Decimal(100)


def is_in_effect(promo: Promo, on: date | None = None) -> bool:
    # Kedua ujung rentang tanggal ikut: promo yang berakhir hari ini berlaku sampai tutup.
    day = on or clock.today()
    return bool(promo.is_active) and promo.starts_on <= day <= promo.ends_on


def in_effect(on: date | None = None) -> ColumnElement[bool]:
    day = on or clock.today()
    return Promo.is_active & (Promo.starts_on <= day) & (Promo.ends_on >= day)


def discount_of(
    promo: Promo, lines: list[tuple[str, Decimal]], subtotal: Decimal, on: date | None = None, ignore_switch: bool = False
) -> Decimal:
    # `ignore_switch` untuk penjualan yang terjadi sebelum promo dimatikan.
    in_effect = promo.starts_on <= (on or clock.today()) <= promo.ends_on if ignore_switch else is_in_effect(promo, on)
    if not in_effect:
        return ZERO
    if promo.kind == KIND_BASIC:
        basis = subtotal
    elif promo.kind == KIND_TOTAL:
        if promo.minimum_spend is not None and subtotal < promo.minimum_spend:
            return ZERO
        basis = subtotal
    elif promo.kind == KIND_PRODUCT:
        product_ids = set(promo.product_ids or [])
        if not product_ids:
            return ZERO
        basis = sum((amount for menu_id, amount in lines if menu_id in product_ids), ZERO)
        if basis <= 0:
            return ZERO
    else:
        return ZERO

    if promo.discount_type == TYPE_PERCENT:
        return round_rupiah(basis * promo.value / PERCENT)
    if promo.discount_type == TYPE_NOMINAL:
        return min(promo.value, basis)
    return ZERO
