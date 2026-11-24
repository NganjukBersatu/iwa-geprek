"""The reading as every client receives it, so the tablet and the management web fill their forms from one shape."""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.core.receipts.ingredients import NO_MATCH, IngredientMatch, IngredientRef
from app.core.receipts.reading import ReceiptReading


class IngredientRefOut(BaseModel):
    id: str
    name: str
    unit_id: str | None
    unit_name: str | None


class ReceiptLineOut(BaseModel):
    name: str
    amount: Decimal
    quantity: int | None
    # Filled only when the name is surely one ingredient of the branch; otherwise the close ones are offered instead.
    ingredient: IngredientRefOut | None
    suggestions: list[IngredientRefOut]


class ReceiptReadingOut(BaseModel):
    store: str | None
    bought_on: date | None
    total: Decimal | None
    items: list[ReceiptLineOut]
    text: list[str]


def _ref_out(ref: IngredientRef) -> IngredientRefOut:
    return IngredientRefOut(id=ref.id, name=ref.name, unit_id=ref.unit_id, unit_name=ref.unit_name)


def reading_out(reading: ReceiptReading, matches: list[IngredientMatch] | None = None) -> ReceiptReadingOut:
    """[matches] runs alongside the items, one per line."""
    found = matches or [NO_MATCH for _ in reading.items]
    return ReceiptReadingOut(
        store=reading.store,
        bought_on=reading.bought_on,
        total=reading.total,
        items=[
            ReceiptLineOut(
                name=line.name,
                amount=line.amount,
                quantity=line.quantity,
                ingredient=_ref_out(match.picked) if match.picked else None,
                suggestions=[_ref_out(ref) for ref in match.suggestions],
            )
            for line, match in zip(reading.items, found, strict=True)
        ],
        text=list(reading.text),
    )
