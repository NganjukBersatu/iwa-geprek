"""The one door for writing the stock of resold items: the web admin and the tablet both come through here."""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import stock_balances
from app.core.errors import DomainError
from app.core.resale_stock import messages
from app.core.resale_stock.constants import COST_PLACES, DEFAULT_COUNT_NOTE, MAX_NOTE_LENGTH, NOT_FOUND, STATUS_LOW, STATUS_OUT, STATUS_SAFE
from app.models.menu_item import MenuItem
from app.models.user import User
from app.models.stock import STOCK_ADJUSTMENT, STOCK_IN, StockCard, StockItem


def status_of(balance: Decimal, minimum: Decimal) -> str:
    if balance <= 0:
        return STATUS_OUT
    if minimum > 0 and balance <= minimum:
        return STATUS_LOW
    return STATUS_SAFE


def moving_average(old_balance: Decimal, old_cost: Decimal | None, qty: Decimal, unit_price: Decimal | None) -> Decimal | None:
    """Only a purchase with a price moves the average; sales, deliveries without a receipt, adjustments and counts inherit the one before."""
    if unit_price is None or qty <= 0:
        return old_cost
    base = max(old_balance, Decimal(0))
    units = base + qty
    if units <= 0:
        return old_cost
    # Rounded to the rupiah, since the profit it feeds is shown in rupiah and a fraction that is never shown only makes totals disagree.
    return ((base * (old_cost or Decimal(0)) + qty * unit_price) / units).quantize(COST_PLACES)


def balance_of(db: Session, outlet_id: str, menu_item_id: str) -> Decimal:
    balance = db.scalar(select(StockItem.balance).where(StockItem.outlet_id == outlet_id, StockItem.menu_item_id == menu_item_id))
    return Decimal(str(balance or 0))


def _latest_cost(db: Session, outlet_id: str, menu_item_id: str) -> Decimal | None:
    """Read from the newest card that has one: one row, not the whole history, since the cost is read on every sale."""
    return db.scalar(
        select(StockCard.cost_after)
        .where(StockCard.outlet_id == outlet_id, StockCard.menu_item_id == menu_item_id, StockCard.cost_after.is_not(None))
        .order_by(StockCard.created_at.desc(), StockCard.id.desc())
        .limit(1)
    )


def managed_menu(db: Session, outlet_id: str, menu_item_id: str) -> MenuItem:
    """Every movement a person records goes through here, or the 'item received' list would hold the whole catalog."""
    menu = db.get(MenuItem, menu_item_id)
    if menu is None:
        raise DomainError(messages.MENU_NOT_FOUND, status=NOT_FOUND)
    managed = db.scalar(select(StockItem.id).where(StockItem.outlet_id == outlet_id, StockItem.menu_item_id == menu_item_id))
    if managed is None:
        raise DomainError(messages.not_marked(menu.name))
    return menu


def _write(db: Session, outlet_id: str, menu: MenuItem, kind: str, qty: Decimal, user: User, unit_price: Decimal | None = None, note: str | None = None) -> StockCard:
    cost = moving_average(balance_of(db, outlet_id, menu.id), _latest_cost(db, outlet_id, menu.id), qty, unit_price)
    card = StockCard(
        outlet_id=outlet_id,
        menu_item_id=menu.id,
        # A snapshot of the name, as on order lines, so the history stays readable after the menu is deleted.
        menu_item_name=menu.name,
        kind=kind,
        qty=qty,
        unit_price=unit_price,
        cost_after=cost,
        note=(note or "").strip() or None,
        user_id=user.id,
    )
    db.add(card)
    return card


def receive(db: Session, user: User, outlet_id: str, menu_item_id: str, qty: Decimal, unit_price: Decimal | None, note: str | None) -> StockCard:
    card = _write(db, outlet_id, managed_menu(db, outlet_id, menu_item_id), STOCK_IN, qty, user, unit_price, note)
    db.commit()
    return card


def adjust(db: Session, user: User, outlet_id: str, menu_item_id: str, qty: Decimal, note: str) -> StockCard:
    if qty == 0:
        raise DomainError(messages.ZERO_ADJUSTMENT)
    card = _write(db, outlet_id, managed_menu(db, outlet_id, menu_item_id), STOCK_ADJUSTMENT, qty, user, None, note)
    db.commit()
    return card


def count(db: Session, user: User, outlet_id: str, counted: list[tuple[str, Decimal]], note: str | None) -> list[tuple[MenuItem, Decimal, Decimal]]:
    """The difference is written as an adjustment, not by overwriting the balance; an item that matches writes nothing."""
    result: list[tuple[MenuItem, Decimal, Decimal]] = []
    # Each item is flushed on its own below, so every row is locked up front, in order, before the first one moves.
    stock_balances.hold(db, [], [(outlet_id, menu_item_id) for menu_item_id, _ in counted])
    for menu_item_id, physical in counted:
        menu = managed_menu(db, outlet_id, menu_item_id)
        system = balance_of(db, outlet_id, menu.id)
        difference = physical - system
        if difference != 0:
            _write(db, outlet_id, menu, STOCK_ADJUSTMENT, difference, user, None, ((note or DEFAULT_COUNT_NOTE).strip())[:MAX_NOTE_LENGTH])
            db.flush()
        result.append((menu, system, physical))
    db.commit()
    return result
