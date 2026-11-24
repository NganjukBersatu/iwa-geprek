"""The one door for writing an ingredient's stock movements: the web admin and the tablet both come through here.

Stock moves by quantity only; what was paid is an expense, recorded once on the expense screen.
"""
import uuid
from decimal import Decimal

from sqlalchemy import ColumnElement, and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.errors import DomainError
from app.core.ingredients import messages
from app.core.ingredients.causes import BY_CODE, OTHER, USAGE_BY_CODE
from app.models.ingredient import INGREDIENT_ADJUSTMENT, INGREDIENT_IN, INGREDIENT_OUT, INGREDIENT_RND, INGREDIENT_WASTE, Ingredient, IngredientCard
from app.models.user import User

NOT_FOUND = 404
CONFLICT = 409


def tidy(text: str | None) -> str | None:
    cleaned = (text or "").strip()
    return cleaned or None


def own_ingredient(db: Session, outlet_id: str, ingredient_id: str) -> Ingredient:
    """An ingredient of another branch answers as missing, so its existence is not revealed."""
    row = db.get(Ingredient, ingredient_id)
    if row is None or row.outlet_id != outlet_id:
        raise DomainError(messages.INGREDIENT_NOT_FOUND, status=NOT_FOUND)
    return row


def _write(
    db: Session, user: User, outlet_id: str, ingredient_id: str, kind: str, qty: Decimal, note: str | None, cause: str | None = None, client_id: str | None = None
) -> IngredientCard:
    ingredient = own_ingredient(db, outlet_id, ingredient_id)
    card = IngredientCard(
        id=str(uuid.uuid4()),
        outlet_id=outlet_id,
        ingredient_id=ingredient.id,
        ingredient_name=ingredient.name,
        kind=kind,
        qty=qty,
        cause=cause,
        user_id=user.id,
        note=tidy(note),
        client_id=client_id,
    )
    db.add(card)
    try:
        db.commit()
    except IntegrityError:
        # Dua kiriman berkunci sama bersamaan: yang kalah mengembalikan kartu milik yang menang.
        db.rollback()
        found = _by_key(db, outlet_id, client_id)
        if found is None:
            raise
        return found
    return card


def _by_key(db: Session, outlet_id: str, client_id: str | None) -> IngredientCard | None:
    if not client_id:
        return None
    return db.scalar(select(IngredientCard).where(IngredientCard.outlet_id == outlet_id, IngredientCard.client_id == client_id))


def receive(db: Session, user: User, outlet_id: str, ingredient_id: str, qty: Decimal, note: str | None) -> IngredientCard:
    return _write(db, user, outlet_id, ingredient_id, INGREDIENT_IN, qty, note)


def waste(db: Session, user: User, outlet_id: str, ingredient_id: str, qty: Decimal, cause: str, note: str | None) -> IngredientCard:
    if cause not in BY_CODE:
        raise DomainError(messages.CAUSE_UNKNOWN)
    if cause == OTHER and not tidy(note):
        raise DomainError(messages.OTHER_NEEDS_NOTE)
    return _write(db, user, outlet_id, ingredient_id, INGREDIENT_WASTE, -qty, note, cause)


def trial(db: Session, user: User, outlet_id: str, ingredient_id: str, qty: Decimal, note: str) -> IngredientCard:
    return _write(db, user, outlet_id, ingredient_id, INGREDIENT_RND, -qty, note)


def adjust(db: Session, user: User, outlet_id: str, ingredient_id: str, qty: Decimal, note: str) -> IngredientCard:
    if qty == 0:
        raise DomainError(messages.ZERO_ADJUSTMENT)
    return _write(db, user, outlet_id, ingredient_id, INGREDIENT_ADJUSTMENT, qty, note)


def own_card(db: Session, outlet_id: str | None, card_id: str) -> IngredientCard:
    """A card of another branch answers as missing; no branch given means the caller already limits branches itself."""
    card = db.get(IngredientCard, card_id)
    if card is None or (outlet_id is not None and card.outlet_id != outlet_id):
        raise DomainError(messages.MOVEMENT_NOT_FOUND, status=NOT_FOUND)
    return card


def correct(db: Session, outlet_id: str | None, card_id: str, values: dict) -> IngredientCard:
    """Changes the size or note of one card; a sale's card is left alone, and the direction of a card never flips."""
    card = own_card(db, outlet_id, card_id)
    if card.order_id:
        raise DomainError(messages.FROM_SALE_EDIT)
    if values.get("qty") is not None:
        size = abs(values["qty"])
        if size == 0:
            raise DomainError(messages.ZERO_QUANTITY)
        # An adjustment may go either way; every other kind keeps its own direction.
        card.qty = values["qty"] if card.kind == INGREDIENT_ADJUSTMENT else (size if card.kind == INGREDIENT_IN else -size)
    if "note" in values:
        card.note = tidy(values["note"])
    db.commit()
    return card


def remove(db: Session, outlet_id: str | None, card_id: str) -> None:
    """Only the stock row goes; an expense an old purchase once created stays on the expense screen."""
    card = own_card(db, outlet_id, card_id)
    if card.order_id:
        raise DomainError(messages.FROM_SALE_DELETE)
    if card.count_id:
        raise DomainError(messages.FROM_COUNT_DELETE)
    proof = card.proof_path
    db.delete(card)
    db.commit()
    uploads.discard(db, proof)


PROOF_FOLDER = "bahan-bukti"
PROOF_RULE = uploads.UploadRule(
    kinds=frozenset({uploads.KIND_PHOTO}),
    unreadable_note="Foto ulang buktinya.",
    not_saved="Foto bukti gagal disimpan. Coba lagi.",
)


def set_proof(db: Session, outlet_id: str | None, card_id: str, image: uploads.UploadedFile) -> IngredientCard:
    """Foto nota atau bukti satu catatan; foto lama dibuang setelah yang baru tersimpan."""
    card = own_card(db, outlet_id, card_id)
    path = f"{PROOF_FOLDER}/{card.id}/{uuid.uuid4()}{image.extension}"
    uploads.store(db, path, image, PROOF_RULE)
    previous = card.proof_path
    card.proof_path = path
    db.commit()
    uploads.discard(db, previous)
    return card


def manual_use_clause() -> ColumnElement[bool]:
    """Satu-satunya definisi pemakaian manual: kartu keluar tanpa pesanan dengan sebab pemakaian."""
    return and_(IngredientCard.kind == INGREDIENT_OUT, IngredientCard.order_id.is_(None), IngredientCard.cause.in_(tuple(USAGE_BY_CODE)))


def use(db: Session, user: User, outlet_id: str, ingredient_id: str, qty: Decimal, cause: str, note: str | None, client_id: str | None) -> IngredientCard:
    """Pemakaian harian bahan tidak langsung; kiriman ulang berkunci sama mengembalikan kartu pertama."""
    if cause not in USAGE_BY_CODE:
        raise DomainError(messages.CAUSE_UNKNOWN)
    if cause == OTHER and not tidy(note):
        raise DomainError(messages.OTHER_NEEDS_NOTE)
    ingredient = own_ingredient(db, outlet_id, ingredient_id)
    if not ingredient.is_indirect:
        raise DomainError(messages.NOT_INDIRECT, code="INGREDIENT_NOT_INDIRECT")
    found = _by_key(db, outlet_id, client_id)
    if found is not None:
        if found.ingredient_id != ingredient.id:
            raise DomainError(messages.KEY_OF_OTHER_INGREDIENT, status=CONFLICT, code="IDEMPOTENCY_KEY_REUSED")
        return found
    return _write(db, user, outlet_id, ingredient.id, INGREDIENT_OUT, -qty, note, cause, client_id)
