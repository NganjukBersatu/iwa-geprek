"""HTTP surface of the resold stock; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.resale_stock import ledger
from app.core.auth import readable_outlet_id, require_permission, writable_outlet_id
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.models.user import User
from web.management.stock_items import repository, service
from web.management.stock_items.constants import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    PERMISSION_ADJUST,
    PERMISSION_COUNT,
    PERMISSION_CORRECT,
    PERMISSION_MANAGE,
    PERMISSION_RECEIVE,
    PERMISSION_VIEW,
)
from web.management.stock_items.mappers import card_out, item_out
from web.management.stock_items.schemas import (
    StockAdjustmentIn,
    StockCandidateOut,
    StockCardUpdateIn,
    StockCountIn,
    StockCountLineOut,
    StockCountOut,
    StockReceiptIn,
    StockSettingsIn,
    StockCardOut,
    StockCardPageOut,
    StockItemOut,
    StockListOut,
)

router = APIRouter(prefix="/stock-items", tags=["web-stock-items"])

LISTING = TypeAdapter(StockListOut)
CANDIDATES = TypeAdapter(list[StockCandidateOut])
CARDS = TypeAdapter(StockCardPageOut)


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _card(db: Session, card_id: str) -> StockCardOut:
    found = repository.card_with_user(db, card_id)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return card_out(found[0], found[1])


def _item(db: Session, outlet_id: str, menu_item_id: str) -> StockItemOut:
    line = next(line for line in service.listing(db, outlet_id, False, None) if line.item.menu_item_id == menu_item_id)
    return item_out(line)


@router.get("", response_model=StockListOut)
def list_items(
    only_problems: bool = Query(False, description="Only what is out of stock or running low"),
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    """Branch by branch, never summed: stock added up over branches is not a figure anyone can act on, since the goods sit on different shelves."""
    def build() -> StockListOut:
        items = [item_out(line) for line in service.listing(db, outlet_id, only_problems, sort)]
        return StockListOut(items=items, total=len(items))

    return cache.read("web.stock-items", (outlet_id, only_problems, sort), build, LISTING, cache.LIST_SECONDS)


@router.get("/candidates", response_model=list[StockCandidateOut])
def candidates(outlet_id: str = Depends(writable_outlet_id), db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    """Menus not yet managed. Which of them is really a resold good stays with the owner, since a category cannot tell mineral water from matcha latte."""
    return cache.read(
        "web.stock-items.candidates",
        (outlet_id,),
        lambda: [StockCandidateOut(menu_item_id=menu_id, menu_item_name=name, category=category) for menu_id, name, category in repository.candidates(db, outlet_id)],
        CANDIDATES,
        cache.REFERENCE_SECONDS,
    )


@router.get("/{item_id}", response_model=StockItemOut)
def get_item(item_id: str, db: Session = Depends(get_db), user: User = Depends(require_permission(PERMISSION_VIEW))):
    with _domain_errors():
        line = service.get(db, user.locked_outlet_id, item_id)
    return item_out(line)


@router.get("/{menu_item_id}/cards", response_model=StockCardPageOut)
def item_cards(
    menu_item_id: str,
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    def build() -> StockCardPageOut:
        rows, total = repository.cards_page(db, outlet_id, menu_item_id, sort, page, size)
        return StockCardPageOut(
            items=[card_out(card, name) for card, name in rows], total=total, page=page, size=size, balance=ledger.balance_of(db, outlet_id, menu_item_id)
        )

    return cache.read("web.stock-items.cards", (outlet_id, menu_item_id, sort, page, size), build, CARDS, cache.LIST_SECONDS)


@router.post("/receipts", response_model=StockCardOut, status_code=status.HTTP_201_CREATED)
def receive(
    body: StockReceiptIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_RECEIVE)),
):
    with _domain_errors():
        card = ledger.receive(db, user, outlet_id, body.menu_item_id, body.qty, body.unit_price, body.note)
    return _card(db, card.id)


@router.post("/adjustments", response_model=StockCardOut, status_code=status.HTTP_201_CREATED)
def adjust(
    body: StockAdjustmentIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_ADJUST)),
):
    with _domain_errors():
        card = ledger.adjust(db, user, outlet_id, body.menu_item_id, body.qty, body.note)
    return _card(db, card.id)


@router.post("/counts", response_model=StockCountOut)
def count(
    body: StockCountIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_COUNT)),
):
    with _domain_errors():
        done = ledger.count(db, user, outlet_id, [(line.menu_item_id, line.counted) for line in body.lines], body.note)
    lines = [StockCountLineOut(menu_item_id=menu.id, menu_item_name=menu.name, system_balance=system, counted=counted, difference=counted - system) for menu, system, counted in done]
    return StockCountOut(lines=lines, adjusted=sum(1 for line in lines if line.difference != Decimal(0)))


@router.patch("/cards/{card_id}", response_model=StockCardOut)
def update_card(
    card_id: str,
    body: StockCardUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_CORRECT)),
):
    with _domain_errors():
        service.update_card(db, user.locked_outlet_id, card_id, body.model_dump(exclude_unset=True))
    return _card(db, card_id)


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: str, db: Session = Depends(get_db), user: User = Depends(require_permission(PERMISSION_CORRECT))):
    with _domain_errors():
        service.delete_card(db, user.locked_outlet_id, card_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{menu_item_id}", response_model=StockItemOut)
def update_settings(
    menu_item_id: str,
    body: StockSettingsIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    """Unit, warning threshold and whether the item is tracked; the first change also marks a menu as a managed good."""
    with _domain_errors():
        service.settings(db, outlet_id, menu_item_id, body.model_dump(exclude_unset=True))
    return _item(db, outlet_id, menu_item_id)


@router.delete("/{menu_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(menu_item_id: str, outlet_id: str = Depends(writable_outlet_id), db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        service.remove(db, outlet_id, menu_item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
