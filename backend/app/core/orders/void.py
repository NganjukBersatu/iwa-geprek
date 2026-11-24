"""The one engine of a cancellation: the order stays as a record, its stock and ingredients come back, the partner bill lets go."""
import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.core import clock
from app.core.orders import stock
from app.models.benefit_usage import BenefitUsage
from app.models.ingredient import INGREDIENT_OUT, IngredientCard
from app.models.order import Order
from app.models.station import StationTask
from app.models.stock import STOCK_IN, STOCK_OUT, StockCard

# Cancelling an order of a closed session, by request or directly, needs this on top of the right to cancel.
PERMISSION_VOID_CLOSED = "order.void_shift_tutup"
NOTE = "Pembatalan"
NOTE_WITH_REASON = "Pembatalan: {reason}"
NO_REASON = "Tidak diisi"
NOTE_LENGTH = 255


def apply_void(db: Session, order: Order, reason: str | None, voided_by_id: str) -> None:
    """The caller decides who may cancel and commits; every path that cancels ends here, so the effects never differ."""
    instant = clock.now()
    order.voided_at = instant
    order.void_reason = (reason or "").strip() or None
    order.voided_by_id = voided_by_id
    db.execute(delete(BenefitUsage).where(BenefitUsage.order_id == order.id))
    # Stasiun yang belum menerima menu pesanan ini tidak punya apa pun untuk dihentikan, jadi tugasnya langsung keluar dari antrean.
    db.execute(
        update(StationTask)
        .where(StationTask.order_id == order.id, StationTask.arrived_at.is_(None), StationTask.finished_at.is_(None), StationTask.acknowledged_at.is_(None))
        .values(acknowledged_at=instant)
        .execution_options(synchronize_session=False)
    )

    stock_note = (NOTE_WITH_REASON.format(reason=order.void_reason) if order.void_reason else NOTE)[:NOTE_LENGTH]
    sold = db.scalars(select(StockCard).where(StockCard.order_id == order.id, StockCard.kind == STOCK_OUT, StockCard.qty < 0)).all()
    for card in sold:
        db.add(
            StockCard(
                id=str(uuid.uuid4()),
                outlet_id=card.outlet_id,
                menu_item_id=card.menu_item_id,
                menu_item_name=card.menu_item_name,
                kind=STOCK_IN,
                qty=-card.qty,
                unit_price=None,
                cost_after=stock.current_cost(db, card.outlet_id, card.menu_item_id) if card.menu_item_id else None,
                order_id=order.id,
                note=stock_note,
                user_id=voided_by_id,
                created_at=instant,
            )
        )

    # Written back as an outgoing card with a positive sign: the ingredient was never bought again, it was only not used up.
    ingredient_note = NOTE_WITH_REASON.format(reason=order.void_reason or NO_REASON)[:NOTE_LENGTH]
    used = db.scalars(
        select(IngredientCard).where(IngredientCard.order_id == order.id, IngredientCard.kind == INGREDIENT_OUT, IngredientCard.qty < 0)
    ).all()
    for card in used:
        db.add(
            IngredientCard(
                id=str(uuid.uuid4()),
                outlet_id=card.outlet_id,
                ingredient_id=card.ingredient_id,
                ingredient_name=card.ingredient_name,
                kind=INGREDIENT_OUT,
                qty=-card.qty,
                order_id=order.id,
                note=ingredient_note,
                user_id=voided_by_id,
                created_at=instant,
            )
        )
