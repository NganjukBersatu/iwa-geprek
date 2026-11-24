"""Stok barang jual-ulang di tablet: aturannya ada di app.core.resale_stock, bersama dengan web admin.

Bacaan di sini tidak pernah di-cache: stok berubah di setiap penjualan dan orang yang menghitung harus melihat angka saat itu.
"""
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import require_gate, require_permission
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.resale_stock import ledger as resale_stock
from app.core.recorded_filters import recorded_filters
from app.core.search import contains
from app.models.category import Unit
from app.models.device import Device
from app.models.menu_item import MenuItem
from app.models.user import User
from app.models.stock import STOCK_ADJUSTMENT, STOCK_IN, StockCard, StockItem
from app.operational.device import tablet
from app.operational.resale_stock import constants as c
from app.operational.resale_stock import messages
from app.operational.resale_stock.schemas import (
    TabletResaleAdjustmentIn,
    TabletResaleCountIn,
    TabletResaleCountOut,
    TabletResaleItemOut,
    TabletResaleItemPageOut,
    TabletResaleMovementOut,
    TabletResaleMovementPageOut,
    TabletResaleReceiptIn,
)
from app.operational.stock.constants import HISTORY_GATE, PERMISSION_ADJUST, PERMISSION_COUNT, PERMISSION_RECEIVE, PICK_GATE

router = APIRouter(prefix="/resale-stock", tags=["v2-operational-resale-stock"])

KINDS = {c.KIND_RECEIPT: STOCK_IN, c.KIND_ADJUSTMENT: STOCK_ADJUSTMENT}
SORT_PATTERN = "^-?(time|name)$"
NAME_SORT_PATTERN = "^-?name$"


def _movement_order(sort: str | None):
    """Waktu atau nama barang, naik atau turun; tanpa pilihan, yang terbaru dulu."""
    value = sort or "-time"
    column = StockCard.menu_item_name if value.lstrip("-") == "name" else StockCard.created_at
    return (column.desc() if value.startswith("-") else column.asc(), StockCard.id)


KIND_PATTERN = f"^({c.KIND_RECEIPT}|{c.KIND_ADJUSTMENT})$"


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _movement(card: StockCard, unit: str | None, user_name: str | None) -> TabletResaleMovementOut:
    return TabletResaleMovementOut(
        id=card.id, menu_item_name=card.menu_item_name, unit=unit, qty=card.qty, kind=card.kind, note=card.note, user_name=user_name, created_at=card.created_at
    )


def _movement_query():
    return (
        select(StockCard, Unit.name, func.coalesce(User.name, User.username))
        .outerjoin(StockItem, (StockItem.outlet_id == StockCard.outlet_id) & (StockItem.menu_item_id == StockCard.menu_item_id))
        .outerjoin(Unit, Unit.id == StockItem.unit_id)
        .outerjoin(User, User.id == StockCard.user_id)
    )


def _one(db: Session, card_id: str) -> TabletResaleMovementOut:
    return _movement(*db.execute(_movement_query().where(StockCard.id == card_id)).one())


@router.get("/items", response_model=TabletResaleItemPageOut)
def list_items(
    search: str | None = Query(None, max_length=c.MAX_SEARCH_LENGTH, description="Bagian dari nama barang"),
    sort: str | None = Query(None, pattern=NAME_SORT_PATTERN, description="name, or -name for descending; no choice means A to Z"),
    page: int = Query(1, ge=1),
    size: int = Query(c.DEFAULT_PAGE_SIZE, ge=1, le=c.MAX_PAGE_SIZE),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(PICK_GATE)),
):
    """Barang jual-ulang yang dilacak di cabang tablet, urut nama, beserta stok saat ini."""
    filters = [StockItem.outlet_id == device.outlet_id, StockItem.is_tracked.is_(True)]
    term = (search or "").strip()
    if term:
        filters.append(contains(MenuItem.name, term))
    total = db.scalar(select(func.count()).select_from(StockItem).join(MenuItem, MenuItem.id == StockItem.menu_item_id).where(*filters)) or 0
    rows = db.execute(
        select(StockItem.menu_item_id, MenuItem.name, Unit.name, StockItem.balance, StockItem.minimum)
        .join(MenuItem, MenuItem.id == StockItem.menu_item_id)
        .outerjoin(Unit, Unit.id == StockItem.unit_id)
        .where(*filters)
        .order_by(MenuItem.name.desc() if sort == "-name" else MenuItem.name.asc(), StockItem.menu_item_id)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    items = []
    for menu_item_id, name, unit, balance, minimum in rows:
        stock, floor = Decimal(str(balance or 0)), Decimal(str(minimum or 0))
        items.append(TabletResaleItemOut(menu_item_id=menu_item_id, name=name, unit=unit, stock=stock, minimum=floor, status=resale_stock.status_of(stock, floor)))
    return TabletResaleItemPageOut(items=items, total=total, page=page, size=size)


@router.get("/movements", response_model=TabletResaleMovementPageOut)
def list_movements(
    kind: str = Query(..., pattern=KIND_PATTERN),
    sort: str | None = Query(None, pattern=SORT_PATTERN, description="time or name; a leading minus means descending, and no choice means newest first"),
    start: Day | None = Query(None, description="Hari bisnis pertama; berpasangan dengan end"),
    end: Day | None = Query(None, description="Hari bisnis terakhir, termasuk"),
    user_id: str | None = Query(None, max_length=c.MAX_ID_LENGTH, description="Hanya catatan orang ini"),
    page: int = Query(1, ge=1),
    size: int = Query(c.DEFAULT_PAGE_SIZE, ge=1, le=c.MAX_PAGE_SIZE),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(HISTORY_GATE)),
):
    """Catatan terbaru satu jenis di cabang tablet, supaya orang melihat yang baru ditulisnya."""
    with _domain_errors():
        filters = [StockCard.outlet_id == device.outlet_id, StockCard.kind == KINDS[kind], *recorded_filters(StockCard, start, end, user_id)]
    total = db.scalar(select(func.count()).select_from(StockCard).where(*filters)) or 0
    rows = db.execute(_movement_query().where(*filters).order_by(*_movement_order(sort)).offset((page - 1) * size).limit(size)).all()
    return TabletResaleMovementPageOut(items=[_movement(*row) for row in rows], total=total, page=page, size=size)


@router.post("/receipts", response_model=TabletResaleMovementOut, status_code=status.HTTP_201_CREATED)
def receive(body: TabletResaleReceiptIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(PERMISSION_RECEIVE))):
    """Jumlah saja; harga beli dicatat sekali di pengeluaran, jadi HPP rata-rata tidak bergeser dari sini."""
    with _domain_errors():
        card = resale_stock.receive(db, user, device.outlet_id, body.menu_item_id, body.qty, None, body.note)
    return _one(db, card.id)


@router.post("/adjustments", response_model=TabletResaleMovementOut, status_code=status.HTTP_201_CREATED)
def adjust(body: TabletResaleAdjustmentIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(PERMISSION_ADJUST))):
    with _domain_errors():
        card = resale_stock.adjust(db, user, device.outlet_id, body.menu_item_id, body.qty, body.note)
    return _one(db, card.id)


@router.post("/counts", response_model=TabletResaleCountOut, status_code=status.HTTP_201_CREATED)
def count(body: TabletResaleCountIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(PERMISSION_COUNT))):
    ids = [line.menu_item_id for line in body.lines]
    if len(set(ids)) != len(ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.DUPLICATE_ITEM)
    with _domain_errors():
        done = resale_stock.count(db, user, device.outlet_id, [(line.menu_item_id, line.counted) for line in body.lines], body.note)
    return TabletResaleCountOut(counted=len(done), adjusted=sum(1 for _, system, physical in done if physical != system))
