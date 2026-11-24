"""One-line summary of what an order holds, such as "2x Latte (Ice) + Boba x2, 1x Es Teh"."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order_item import OrderItem
from app.models.order_item_option import EXTRA, VARIANT, OrderItemOption


def line_text(menu_name: str, qty: int, options: list[OrderItemOption]) -> str:
    """Menu name, then variants in brackets, then extras."""
    variants = [option.name for option in options if option.kind == VARIANT]
    extras = [f"{option.name} x{option.qty}" if option.qty > 1 else option.name for option in options if option.kind == EXTRA]
    text = f"{qty}x {menu_name}"
    if variants:
        text += f" ({', '.join(variants)})"
    if extras:
        text += f" + {', '.join(extras)}"
    return text


def summaries(db: Session, order_ids: list[str]) -> dict[str, str]:
    """Summary per order id, read with one query for the lines and one for their options."""
    if not order_ids:
        return {}
    rows = db.execute(
        select(OrderItem.id, OrderItem.order_id, OrderItem.qty, OrderItem.menu_item_name)
        .where(OrderItem.order_id.in_(order_ids))
        .order_by(OrderItem.order_id)
    ).all()
    options_by_line: dict[str, list[OrderItemOption]] = {}
    if rows:
        for option in db.scalars(
            select(OrderItemOption).where(OrderItemOption.order_item_id.in_([row[0] for row in rows]))
        ).all():
            options_by_line.setdefault(option.order_item_id, []).append(option)
    parts: dict[str, list[str]] = {}
    for line_id, order_id, qty, name in rows:
        parts.setdefault(order_id, []).append(line_text(name, qty, options_by_line.get(line_id, [])))
    return {order_id: ", ".join(texts) for order_id, texts in parts.items()}
