from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class CategorySalesOut(BaseModel):
    category: str
    qty: int
    revenue: Decimal
    menu_count: int
    revenue_percent: Decimal
    # Kosong bila tidak ada baris bermodal; cost_complete salah berarti sebagian baris tanpa modal sehingga laba terbaca lebih besar.
    profit: Decimal | None
    cost_complete: bool
    previous_revenue: Decimal
    # Kosong bila omzet periode sebelumnya nol.
    revenue_change_percent: Decimal | None


class MenuSalesOut(BaseModel):
    menu_item_id: str | None
    name: str
    category: str
    qty: int
    revenue: Decimal
    profit: Decimal | None
    cost_complete: bool


class UnsoldMenuOut(BaseModel):
    menu_item_id: str
    name: str
    category: str | None
    price: Decimal
    is_available: bool
    last_sold_at: datetime | None
    created_at: datetime


class CategoriesOut(BaseModel):
    start: date
    end: date
    previous_start: date
    previous_end: date
    total_revenue: Decimal
    previous_total_revenue: Decimal
    orders_without_lines: int
    revenue_without_lines: Decimal
    categories: list[CategorySalesOut]
    # Rincian per menu untuk menelusuri satu kategori; disaring di layar menurut nama kategori.
    menus: list[MenuSalesOut]
    total_menu_count: int
    sold_menu_count: int
    unsold: list[UnsoldMenuOut]
