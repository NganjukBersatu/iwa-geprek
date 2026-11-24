"""Receiving ingredients and correcting the ledger; the balance of an ingredient is always the sum of its rows."""
from sqlalchemy.orm import Session

from app.core.ingredients import ledger
from app.models.ingredient import IngredientCard
from app.models.user import User
from app.core.uploads import UploadedFile


def update(db: Session, user: User, card_id: str, values: dict) -> IngredientCard:
    return ledger.correct(db, user.locked_outlet_id, card_id, values)


def delete(db: Session, user: User, card_id: str) -> None:
    ledger.remove(db, user.locked_outlet_id, card_id)


def set_proof(db: Session, user: User, card_id: str, image: UploadedFile) -> IngredientCard:
    return ledger.set_proof(db, user.locked_outlet_id, card_id, image)


def read(db: Session, user: User, card_id: str) -> IngredientCard:
    """One card for its page; a card of another branch answers as missing."""
    return ledger.own_card(db, user.locked_outlet_id, card_id)

