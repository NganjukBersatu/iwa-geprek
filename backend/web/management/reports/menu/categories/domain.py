"""What the categories service hands to the mappers."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class CategorySales:
    category: str
    qty: int
    revenue: Decimal
    menu_count: int
    revenue_percent: Decimal
    # Omzet dikurangi modal baris yang modalnya tercatat; None bila tidak satu baris pun punya modal.
    profit: Decimal | None
    # Benar bila setiap baris kategori ini punya modal, sehingga laba tidak terlalu besar.
    cost_complete: bool
    previous_revenue: Decimal
    # Perubahan omzet terhadap periode sebelumnya; None bila periode sebelumnya nol.
    revenue_change_percent: Decimal | None


@dataclass(frozen=True)
class MenuSales:
    menu_item_id: str | None
    name: str
    category: str
    qty: int
    revenue: Decimal
    profit: Decimal | None
    cost_complete: bool


@dataclass(frozen=True)
class UnsoldMenu:
    menu_item_id: str
    name: str
    category: str | None
    price: Decimal
    is_available: bool
    last_sold_at: datetime | None
    # Kapan menu masuk katalog, supaya menu baru tidak dinilai sama dengan menu lama yang tidak laku.
    created_at: datetime


@dataclass(frozen=True)
class Categories:
    start: date
    end: date
    previous_start: date
    previous_end: date
    total_revenue: Decimal
    previous_total_revenue: Decimal
    orders_without_lines: int
    revenue_without_lines: Decimal
    categories: list[CategorySales]
    menus: list[MenuSales]
    total_menu_count: int
    sold_menu_count: int
    unsold: list[UnsoldMenu]
