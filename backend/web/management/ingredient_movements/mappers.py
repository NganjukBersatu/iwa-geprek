from app.core.http import static_url
from app.models.ingredient import IngredientCard
from app.core.ingredients.causes import BY_CODE
from web.management.ingredient_movements.schemas import MovementOut


def movement_out(card: IngredientCard, user_name: str | None, unit: str | None, base_url: str) -> MovementOut:
    return MovementOut(
        id=card.id,
        outlet_id=card.outlet_id,
        business_day=card.business_day,
        ingredient_id=card.ingredient_id,
        ingredient_name=card.ingredient_name,
        kind=card.kind,
        unit=unit or "",
        qty=card.qty,
        cause=card.cause,
        cause_label=BY_CODE[card.cause].label if card.cause in BY_CODE else None,
        human_error=BY_CODE[card.cause].human_error if card.cause in BY_CODE else None,
        proof_url=static_url(base_url, card.proof_path),
        order_id=card.order_id,
        count_id=card.count_id,
        note=card.note,
        user_id=card.user_id,
        user_name=user_name,
        created_at=card.created_at,
    )
