"""Resold menu items whose quantity a branch tracks; a sale writes one outgoing card."""
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.models.menu_item import MenuItem
from app.models.stock import STOCK_OUT, StockCard, StockItem


def is_tracked(db: Session, outlet_id: str, menu_item_id: str) -> bool:
    """False for menus that never had a stock row: made-to-order drinks are not counted, so a balance would mean nothing."""
    tracked = db.scalar(select(StockItem.is_tracked).where(StockItem.outlet_id == outlet_id, StockItem.menu_item_id == menu_item_id))
    return bool(tracked)


def current_cost(db: Session, outlet_id: str, menu_item_id: str) -> Decimal | None:
    """Moving-average cost from the newest card; None means never bought with a receipt, which is not zero."""
    return db.scalar(
        select(StockCard.cost_after)
        .where(StockCard.outlet_id == outlet_id, StockCard.menu_item_id == menu_item_id, StockCard.cost_after.is_not(None))
        .order_by(StockCard.created_at.desc(), StockCard.id.desc())
        .limit(1)
    )


def record_sale(db: Session, outlet_id: str, menu: MenuItem, qty: int, order_id: str, user_id: str | None, note: str | None) -> None:
    """A sale does not move the average cost, so the card inherits the one before it; the caller commits."""
    db.add(
        StockCard(
            id=str(uuid.uuid4()),
            outlet_id=outlet_id,
            menu_item_id=menu.id,
            menu_item_name=menu.name,
            kind=STOCK_OUT,
            qty=-Decimal(qty),
            unit_price=None,
            cost_after=current_cost(db, outlet_id, menu.id),
            order_id=order_id,
            note=note,
            user_id=user_id,
            created_at=clock.now(),
        )
    )
