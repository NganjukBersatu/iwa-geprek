from app.models.stock import StockCard
from web.management.stock_items.domain import StockLine
from web.management.stock_items.schemas import StockCardOut, StockItemOut


def item_out(line: StockLine) -> StockItemOut:
    return StockItemOut(
        id=line.item.id,
        outlet_id=line.item.outlet_id,
        outlet_name=line.outlet_name,
        menu_item_id=line.item.menu_item_id,
        menu_item_name=line.name,
        unit_id=line.item.unit_id,
        unit=line.unit,
        minimum=line.item.minimum,
        is_tracked=line.item.is_tracked,
        balance=line.balance,
        cost=line.cost,
        inventory_value=line.inventory_value,
        status=line.status,
    )


def card_out(card: StockCard, user_name: str | None) -> StockCardOut:
    return StockCardOut(
        id=card.id,
        menu_item_id=card.menu_item_id,
        menu_item_name=card.menu_item_name,
        kind=card.kind,
        qty=card.qty,
        unit_price=card.unit_price,
        cost_after=card.cost_after,
        note=card.note,
        order_id=card.order_id,
        user_id=card.user_id,
        user_name=user_name,
        created_at=card.created_at,
    )
