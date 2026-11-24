"""HTTP surface of the ingredient ledger; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import bulk, cache, uploads
from app.core.auth import readable_outlet_id, require_gate, require_permission, writable_outlet_id
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.ingredients import ledger
from app.core.ingredients.causes import CAUSES
from app.core.sorting import Sort
from app.core.http import public_base_url
from app.models.user import User
from web.management.ingredient_movements import repository, service
from web.management.ingredient_movements.constants import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_SEARCH_LENGTH,
    PERMISSION_ADJUST,
    PERMISSION_CORRECT,
    PERMISSION_RECEIVE,
    PERMISSION_VIEW,
    PROOF_GATE,
)
from web.management.ingredient_movements.mappers import movement_out
from web.management.ingredient_movements.schemas import (
    AdjustmentIn,
    CauseOut,
    Kind,
    MovementOut,
    MovementPageOut,
    MovementUpdateIn,
    ReceiptIn,
    TrialIn,
    WasteIn,
)
from web.management.reports.common import month_to_date

router = APIRouter(prefix="/ingredient-movements", tags=["web-ingredient-movements"])

PAGE = TypeAdapter(MovementPageOut)


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _one(db: Session, card_id: str) -> MovementOut:
    found = repository.with_user(db, card_id)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return movement_out(found[0], found[1], found[2], public_base_url())


@router.get("", response_model=MovementPageOut)
def list_movements(
    kind: Kind | None = Query(None),
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the ingredient name or the note"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    with _domain_errors():
        first, last = month_to_date(start, end)
    term = (search or "").strip() or None
    base_url = public_base_url()

    def build() -> MovementPageOut:
        rows, total, human, natural = repository.page_of(db, first, last, outlet_id, kind, term, sort, page, size)
        return MovementPageOut(
            start=first,
            end=last,
            items=[movement_out(card, name, unit, base_url) for card, name, unit in rows],
            total=total,
            human_error_count=human,
            natural_count=natural,
            page=page,
            size=size,
        )

    with _domain_errors():
        # Free text has no end of values, so it is never a key.
        if term:
            return build()
        return cache.read("web.ingredient-movements", (kind, first, last, outlet_id, sort, page, size, base_url), build, PAGE, cache.LIST_SECONDS)


@router.get("/causes", response_model=list[CauseOut])
def waste_causes(_: User = Depends(require_permission(PERMISSION_VIEW))):
    return [CauseOut(code=cause.code, label=cause.label, human_error=cause.human_error) for cause in CAUSES]


@router.post("/waste", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def record_waste(
    body: WasteIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_ADJUST)),
):
    with _domain_errors():
        card = ledger.waste(db, user, outlet_id, body.ingredient_id, body.qty, body.cause, body.note)
    return _one(db, card.id)


@router.post("/trials", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def record_trial(
    body: TrialIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_ADJUST)),
):
    with _domain_errors():
        card = ledger.trial(db, user, outlet_id, body.ingredient_id, body.qty, body.note)
    return _one(db, card.id)


@router.post("/adjustments", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def record_adjustment(
    body: AdjustmentIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_ADJUST)),
):
    with _domain_errors():
        card = ledger.adjust(db, user, outlet_id, body.ingredient_id, body.qty, body.note)
    return _one(db, card.id)


@router.post("/receipts", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def receive(
    body: ReceiptIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_RECEIVE)),
):
    with _domain_errors():
        card = ledger.receive(db, user, outlet_id, body.ingredient_id, body.qty, body.note)
    return _one(db, card.id)


@router.get("/{card_id}", response_model=MovementOut)
def get_movement(card_id: str, db: Session = Depends(get_db), user: User = Depends(require_permission(PERMISSION_VIEW))):
    with _domain_errors():
        service.read(db, user, card_id)
    return _one(db, card_id)


@router.patch("/{card_id}", response_model=MovementOut)
def update_movement(
    card_id: str,
    body: MovementUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_CORRECT)),
):
    with _domain_errors():
        service.update(db, user, card_id, body.model_dump(exclude_unset=True))
    return _one(db, card_id)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movement(card_id: str, db: Session = Depends(get_db), user: User = Depends(require_permission(PERMISSION_CORRECT))):
    with _domain_errors():
        service.delete(db, user, card_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{card_id}/proof", response_model=MovementOut)
async def replace_proof(
    card_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(PROOF_GATE)),
):
    """Attaching proof is part of recording it: a purchase note by whoever may receive, waste or trial proof by whoever may adjust."""
    with _domain_errors():
        image = await uploads.receive(file, ledger.PROOF_RULE)
        service.set_proof(db, user, card_id, image)
    return _one(db, card_id)


bulk.add_bulk_routes(
    router,
    PERMISSION_RECEIVE,
    create_schema=ReceiptIn,
    create=lambda db, body, user, outlet_id: ledger.receive(db, user, outlet_id, body.ingredient_id, body.qty, body.note),
    create_context=writable_outlet_id,
)

waste_bulk = APIRouter(prefix="/waste")
bulk.add_bulk_routes(
    waste_bulk,
    PERMISSION_ADJUST,
    create_schema=WasteIn,
    create=lambda db, body, user, outlet_id: ledger.waste(db, user, outlet_id, body.ingredient_id, body.qty, body.cause, body.note),
    create_context=writable_outlet_id,
)
trials_bulk = APIRouter(prefix="/trials")
bulk.add_bulk_routes(
    trials_bulk,
    PERMISSION_ADJUST,
    create_schema=TrialIn,
    create=lambda db, body, user, outlet_id: ledger.trial(db, user, outlet_id, body.ingredient_id, body.qty, body.note),
    create_context=writable_outlet_id,
)
router.include_router(waste_bulk)
router.include_router(trials_bulk)
