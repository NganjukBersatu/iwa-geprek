"""The list and the settings of the resold items a branch counts; writing the stock itself is the core ledger's."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.catalog import fixed_cost
from app.core.errors import DomainError
from app.core.resale_stock import messages as core_messages
from app.core.resale_stock.constants import STATUS_ORDER, STATUS_SAFE
from app.core.resale_stock.ledger import status_of
from app.core.sorting import RowSorting
from app.models.stock import STOCK_ADJUSTMENT, STOCK_IN, StockCard, StockItem
from web.management.stock_items import messages, repository
from web.management.stock_items.constants import NOT_FOUND
from web.management.stock_items.domain import StockLine


SORTING: RowSorting[StockLine] = RowSorting(
    keys={
        "name": lambda line: line.name,
        "outlet": lambda line: line.outlet_name,
        "balance": lambda line: line.balance,
        "cost": lambda line: line.cost,
        "value": lambda line: line.inventory_value,
        "status": lambda line: STATUS_ORDER.index(line.status),
    },
    identity=lambda line: f"{line.item.outlet_id}:{line.item.menu_item_id}",
)


def listing(db: Session, outlet_id: str | None, only_problems: bool, sort: str | None) -> list[StockLine]:
    """One branch's items, or every active branch's, branch by branch; balances are never summed across branches.

    Four queries however many branches and items there are: the branches, the items, the balances, the latest costs.
    """
    outlets = repository.outlets(db, outlet_id)
    ids = [outlet.id for outlet in outlets]
    if not ids:
        return []
    items, balances, costs = repository.items_of(db, ids), repository.balances(db, ids), repository.latest_costs(db, ids)
    by_branch: dict[str, list[tuple[StockItem, str, str | None]]] = {outlet.id: [] for outlet in outlets}
    for row in items:
        by_branch[row[0].outlet_id].append(row)
    lines: list[StockLine] = []
    for outlet in outlets:
        for item, name, unit in by_branch[outlet.id]:
            key = (outlet.id, item.menu_item_id)
            balance = balances.get(key, Decimal(0))
            status = status_of(balance, item.minimum)
            if only_problems and status == STATUS_SAFE:
                continue
            lines.append(StockLine(item, outlet.name, name, unit, balance, costs.get(key), status))
    return SORTING.apply(lines, sort)


def get(db: Session, locked_outlet_id: str | None, item_id: str) -> StockLine:
    """One item for its own page; one of another branch answers as missing for someone bound to one branch."""
    item = repository.find_item_by_id(db, item_id)
    if item is None or (locked_outlet_id and item.outlet_id != locked_outlet_id):
        raise DomainError(messages.ITEM_NOT_MANAGED, status=NOT_FOUND)
    for line in listing(db, item.outlet_id, False, None):
        if line.item.id == item.id:
            return line
    raise DomainError(messages.ITEM_NOT_MANAGED, status=NOT_FOUND)


def settings(db: Session, outlet_id: str, menu_item_id: str, values: dict) -> StockItem:
    """The row is made the first time it is needed, so the list holds the items that are really managed and not the whole catalog at zero."""
    menu = repository.find_menu(db, menu_item_id)
    if menu is None:
        raise DomainError(core_messages.MENU_NOT_FOUND, status=NOT_FOUND)
    item = repository.find_item(db, outlet_id, menu_item_id)
    if item is None:
        fixed_cost.ensure_can_hold_stock(db, menu_item_id)
        item = StockItem(outlet_id=outlet_id, menu_item_id=menu_item_id)
        db.add(item)
    if values.get("unit_id") is not None:
        if not repository.unit_exists(db, values["unit_id"]):
            raise DomainError(messages.UNIT_UNKNOWN)
        item.unit_id = values["unit_id"]
    if values.get("minimum") is not None:
        item.minimum = values["minimum"]
    if values.get("is_tracked") is not None:
        item.is_tracked = values["is_tracked"]
    db.commit()
    return item


def remove(db: Session, outlet_id: str, menu_item_id: str) -> None:
    """Removing means removing: the movements go with the item. Turning tracking off keeps the history for whoever wants it."""
    item = repository.find_item(db, outlet_id, menu_item_id)
    if item is None:
        raise DomainError(messages.ITEM_NOT_MANAGED, status=NOT_FOUND)
    repository.delete_item(db, item)
    db.commit()


def _card_in_scope(db: Session, locked_outlet_id: str | None, card_id: str) -> StockCard:
    card = repository.find_card(db, card_id)
    if card is None or (locked_outlet_id and card.outlet_id != locked_outlet_id):
        raise DomainError(messages.CARD_NOT_FOUND, status=NOT_FOUND)
    return card


def update_card(db: Session, locked_outlet_id: str | None, card_id: str, values: dict) -> StockCard:
    """A purchase stays positive, a sale stays negative, an adjustment follows the sign sent."""
    card = _card_in_scope(db, locked_outlet_id, card_id)
    if values.get("qty") is not None:
        size = abs(values["qty"])
        if size == 0:
            raise DomainError(messages.ZERO_QUANTITY)
        card.qty = values["qty"] if card.kind == STOCK_ADJUSTMENT else (size if card.kind == STOCK_IN else -size)
    if values.get("unit_price") is not None:
        card.unit_price = values["unit_price"]
    if "note" in values:
        card.note = (values["note"] or "").strip() or None
    db.commit()
    return card


def delete_card(db: Session, locked_outlet_id: str | None, card_id: str) -> None:
    """The balance follows by itself; what does not is the cost recorded on later cards, which was worked out once when each was written."""
    db.delete(_card_in_scope(db, locked_outlet_id, card_id))
    db.commit()
