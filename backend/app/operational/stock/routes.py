"""Ingredient stock on the tablet: the rules live in app.core.ingredient_ledger and app.core.ingredient_counts, shared with the web.

Reads here are never cached: the stock changes with every sale, and a person counting must see the figure of the moment.
"""
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.orm import Session

from app.core.ingredients import count_requests as close_requests
from app.core.ingredients import counts
from app.core import bulk, uploads
from app.core.ingredients import ledger
from app.core.ingredients import openings
from app.core.auth import require_gate, require_permission
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.http import public_base_url, static_url
from app.core.date_range import Day
from app.core.ingredients.causes import BY_CODE, CAUSES, USAGE_BY_CODE, USAGE_CAUSES
from app.core.recorded_filters import recorded_filters
from app.core.search import contains
from app.core.user_names import user_names
from app.models.category import Category, Unit
from app.models.device import Device
from app.models.ingredient import INGREDIENT_ADJUSTMENT, INGREDIENT_IN, INGREDIENT_OUT, INGREDIENT_RND, INGREDIENT_WASTE, Ingredient, IngredientCard, IngredientCountRequest, RecipeIngredient
from app.models.menu_item import MenuItem
from app.models.user import User
from app.operational.device import tablet, tablet_outlet_id
from app.operational.stock import constants as c
from app.operational.stock.schemas import (
    TabletStockOpeningRowIn,
    TabletStockCauseOut,
    TabletStockCloseRequestIn,
    TabletStockIngredientOut,
    TabletStockIngredientPageOut,
    TabletStockJourneyOut,
    TabletStockMovementOut,
    TabletStockMovementPageOut,
    TabletStockMovementUpdateIn,
    TabletStockOpeningIn,
    TabletStockOpeningPeriodOut,
    TabletStockReceiptIn,
    TabletStockRecipeUseOut,
    TabletStockRecipeUsePageOut,
    TabletStockRequestOut,
    TabletStockTrialIn,
    TabletStockUseIn,
    TabletStockWasteIn,
)

router = APIRouter(prefix="/stock", tags=["v2-operational-stock"])

KINDS = {c.KIND_RECEIPT: INGREDIENT_IN, c.KIND_WASTE: INGREDIENT_WASTE, c.KIND_TRIAL: INGREDIENT_RND, c.KIND_USE: INGREDIENT_OUT}
SORT_PATTERN = "^-?(time|name)$"
NAME_SORT_PATTERN = "^-?name$"
OPENING_FILTER_PATTERN = "^(with|without)$"


def _movement_order(sort: str | None):
    """Waktu atau nama bahan, naik atau turun; tanpa pilihan, yang terbaru dulu."""
    value = sort or "-time"
    column = IngredientCard.ingredient_name if value.lstrip("-") == "name" else IngredientCard.created_at
    return (column.desc() if value.startswith("-") else column.asc(), IngredientCard.id)


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _movement(card: IngredientCard, unit: str | None, user_name: str | None, base_url: str) -> TabletStockMovementOut:
    # Bahan rusak dan pemakaian manual punya daftar sebab sendiri, dan kode "lainnya" ada di keduanya.
    causes = USAGE_BY_CODE if card.kind == INGREDIENT_OUT else BY_CODE
    cause = causes.get(card.cause) if card.cause else None
    return TabletStockMovementOut(
        id=card.id,
        ingredient_id=card.ingredient_id,
        ingredient_name=card.ingredient_name,
        unit=unit,
        qty=card.qty,
        kind=card.kind,
        cause_label=cause.label if cause else None,
        note=card.note,
        user_name=user_name,
        created_at=card.created_at,
        proof_url=static_url(base_url, card.proof_path),
        from_sale=card.order_id is not None,
        from_count=card.count_id is not None,
        from_opening=openings.is_opening_card(card),
    )


def _movement_query():
    return (
        select(IngredientCard, Unit.name, func.coalesce(User.name, User.username))
        .outerjoin(Ingredient, Ingredient.id == IngredientCard.ingredient_id)
        .outerjoin(Unit, Unit.id == Ingredient.unit_id)
        .outerjoin(User, User.id == IngredientCard.user_id)
    )


def _one(db: Session, card_id: str, base_url: str) -> TabletStockMovementOut:
    return _movement(*db.execute(_movement_query().where(IngredientCard.id == card_id)).one(), base_url)


@router.get("/ingredients", response_model=TabletStockIngredientPageOut)
def list_ingredients(
    search: str | None = Query(None, max_length=c.MAX_SEARCH_LENGTH, description="Part of the ingredient name"),
    sort: str | None = Query(None, pattern=NAME_SORT_PATTERN, description="name, or -name for descending; no choice means A to Z"),
    opening: str | None = Query(None, pattern=OPENING_FILTER_PATTERN, description="with: stok awal sudah diisi; without: belum"),
    indirect: bool | None = Query(None, description="true: hanya bahan tidak langsung; false: hanya yang berkurang lewat resep; kosong: keduanya"),
    page: int = Query(1, ge=1),
    size: int = Query(c.DEFAULT_PAGE_SIZE, ge=1, le=c.MAX_PAGE_SIZE),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(c.PICK_GATE)),
):
    """The active ingredients of the tablet's branch with their stock now and the opening of the running period, in name order."""
    start = openings.running_start(db, device.outlet_id)
    filters = [Ingredient.outlet_id == device.outlet_id, Ingredient.is_active.is_(True)]
    if indirect is not None:
        filters.append(Ingredient.is_indirect.is_(indirect))
    term = (search or "").strip()
    if term:
        filters.append(contains(Ingredient.name, term))
    if opening == "with":
        filters.append(openings.has_opening(start, Ingredient.id))
    elif opening == "without":
        filters.append(~openings.has_opening(start, Ingredient.id))
    total = db.scalar(select(func.count()).select_from(Ingredient).where(*filters)) or 0
    rows = db.execute(
        select(Ingredient.id, Ingredient.name, Unit.name, Category.name, Ingredient.balance, Ingredient.minimum, Ingredient.package_size, Ingredient.is_indirect)
        .outerjoin(Unit, Unit.id == Ingredient.unit_id)
        .outerjoin(Category, Category.id == Ingredient.category_id)
        .where(*filters)
        .order_by(Ingredient.name.desc() if sort == "-name" else Ingredient.name.asc(), Ingredient.id)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    filled = openings.openings(db, device.outlet_id, start, [row[0] for row in rows])
    items = [
        TabletStockIngredientOut(
            id=row[0],
            name=row[1],
            unit=row[2],
            category=row[3],
            stock=Decimal(str(row[4] or 0)),
            minimum=Decimal(str(row[5] or 0)),
            opening=filled[row[0]].qty if row[0] in filled else None,
            package_size=Decimal(str(row[6] or 0)),
            is_indirect=bool(row[7]),
        )
        for row in rows
    ]
    return TabletStockIngredientPageOut(items=items, total=total, page=page, size=size)

@router.get("/use-causes", response_model=list[TabletStockCauseOut])
def use_causes(_: User = Depends(require_permission(c.PERMISSION_ADJUST))):
    return [TabletStockCauseOut(code=cause.code, label=cause.label) for cause in USAGE_CAUSES]


@router.get("/causes", response_model=list[TabletStockCauseOut])
def waste_causes(_: User = Depends(require_permission(c.PERMISSION_ADJUST))):
    return [TabletStockCauseOut(code=cause.code, label=cause.label) for cause in CAUSES]


def _kinds_clause(kinds: list[str]) -> ColumnElement[bool]:
    """Pemakaian manual berbagi jenis kartu dengan potongan resep penjualan, jadi dibedakan lewat definisi tunggal di ledger."""
    plain = {KINDS[value] for value in kinds if value != c.KIND_USE}
    wanted = [IngredientCard.kind.in_(plain)] if plain else []
    if c.KIND_USE in kinds:
        wanted.append(ledger.manual_use_clause())
    return or_(*wanted)


@router.get("/movements", response_model=TabletStockMovementPageOut)
def list_movements(
    kind: list[str] = Query(..., min_length=1, max_length=len(KINDS), description="One or more of receipt, waste, trial, use; Rusak dan RnD share one list"),
    search: str | None = Query(None, max_length=c.MAX_SEARCH_LENGTH, description="Part of the ingredient name or the note"),
    sort: str | None = Query(None, pattern=SORT_PATTERN, description="time or name; a leading minus means descending, and no choice means newest first"),
    start: Day | None = Query(None, description="Hari bisnis pertama; berpasangan dengan end"),
    end: Day | None = Query(None, description="Hari bisnis terakhir, termasuk"),
    user_id: str | None = Query(None, max_length=c.MAX_ID_LENGTH, description="Hanya catatan orang ini"),
    page: int = Query(1, ge=1),
    size: int = Query(c.DEFAULT_PAGE_SIZE, ge=1, le=c.MAX_PAGE_SIZE),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(c.HISTORY_GATE)),
):
    """The newest entries of the chosen kinds at the tablet's branch, so a person sees what was just written."""
    unknown = [value for value in kind if value not in KINDS]
    if unknown:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=c.MESSAGE_UNKNOWN_KIND)
    with _domain_errors():
        filters = [IngredientCard.outlet_id == device.outlet_id, _kinds_clause(kind), *recorded_filters(IngredientCard, start, end, user_id)]
    term = (search or "").strip()
    if term:
        filters.append(or_(contains(IngredientCard.ingredient_name, term), contains(IngredientCard.note, term)))
    total = db.scalar(select(func.count()).select_from(IngredientCard).where(*filters)) or 0
    rows = db.execute(
        _movement_query().where(*filters).order_by(*_movement_order(sort)).offset((page - 1) * size).limit(size)
    ).all()
    return TabletStockMovementPageOut(items=[_movement(*row, public_base_url()) for row in rows], total=total, page=page, size=size)


@router.get("/ingredients/{ingredient_id}/movements", response_model=TabletStockMovementPageOut)
def ingredient_movements(
    ingredient_id: str,
    user_id: str | None = Query(None, max_length=c.MAX_ID_LENGTH, description="Hanya catatan orang ini"),
    page: int = Query(1, ge=1),
    size: int = Query(c.DEFAULT_PAGE_SIZE, ge=1, le=c.MAX_PAGE_SIZE),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(c.HISTORY_GATE)),
):
    """Every movement of one ingredient at the tablet's branch, sales and counts included, newest first."""
    with _domain_errors():
        ledger.own_ingredient(db, device.outlet_id, ingredient_id)
    filters = [IngredientCard.outlet_id == device.outlet_id, IngredientCard.ingredient_id == ingredient_id, *recorded_filters(IngredientCard, None, None, user_id)]
    total = db.scalar(select(func.count()).select_from(IngredientCard).where(*filters)) or 0
    rows = db.execute(
        _movement_query().where(*filters).order_by(*_movement_order(None)).offset((page - 1) * size).limit(size)
    ).all()
    return TabletStockMovementPageOut(items=[_movement(*row, public_base_url()) for row in rows], total=total, page=page, size=size)


def _tablet_card(db: Session, outlet_id: str, card_id: str) -> IngredientCard:
    """Kartu penutupan periode hanya diubah admin di web, dan stok awal hanya lewat kartu stok awal."""
    card = ledger.own_card(db, outlet_id, card_id)
    if card.count_id is not None:
        raise DomainError(c.FROM_COUNT_WEB_ONLY, status=c.CONFLICT)
    if openings.is_opening_card(card):
        raise DomainError(c.FROM_OPENING_CARD, status=c.CONFLICT)
    return card


@router.patch("/movements/{card_id}", response_model=TabletStockMovementOut)
def correct_movement(card_id: str, body: TabletStockMovementUpdateIn, device: Device = Depends(tablet), db: Session = Depends(get_db), _: User = Depends(require_permission(c.PERMISSION_CORRECT))):
    changes = body.model_dump(exclude_unset=True)
    with _domain_errors():
        card = _tablet_card(db, device.outlet_id, card_id)
        # The tablet sends a size only, so an adjustment that took stock away keeps taking it away.
        if changes.get("qty") is not None and card.kind == INGREDIENT_ADJUSTMENT and card.qty < 0:
            changes["qty"] = -changes["qty"]
        ledger.correct(db, device.outlet_id, card_id, changes)
    return _one(db, card_id, public_base_url())


@router.delete("/movements/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_movement(card_id: str, device: Device = Depends(tablet), db: Session = Depends(get_db), _: User = Depends(require_permission(c.PERMISSION_CORRECT))):
    with _domain_errors():
        _tablet_card(db, device.outlet_id, card_id)
        ledger.remove(db, device.outlet_id, card_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/receipts", response_model=TabletStockMovementOut, status_code=status.HTTP_201_CREATED)
def receive(body: TabletStockReceiptIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(c.PERMISSION_RECEIVE))):
    with _domain_errors():
        card = ledger.receive(db, user, device.outlet_id, body.ingredient_id, body.qty, body.note)
    return _one(db, card.id, public_base_url())


@router.post("/waste", response_model=TabletStockMovementOut, status_code=status.HTTP_201_CREATED)
def record_waste(body: TabletStockWasteIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(c.PERMISSION_ADJUST))):
    with _domain_errors():
        card = ledger.waste(db, user, device.outlet_id, body.ingredient_id, body.qty, body.cause, body.note)
    return _one(db, card.id, public_base_url())


@router.post("/uses", response_model=TabletStockMovementOut, status_code=status.HTTP_201_CREATED)
def record_use(body: TabletStockUseIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(c.PERMISSION_ADJUST))):
    with _domain_errors():
        card = ledger.use(db, user, device.outlet_id, body.ingredient_id, body.qty, body.cause, body.note, body.client_id)
    return _one(db, card.id, public_base_url())


@router.post("/trials", response_model=TabletStockMovementOut, status_code=status.HTTP_201_CREATED)
def record_trial(body: TabletStockTrialIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(c.PERMISSION_ADJUST))):
    with _domain_errors():
        card = ledger.trial(db, user, device.outlet_id, body.ingredient_id, body.qty, body.note)
    return _one(db, card.id, public_base_url())


# Tidak di-cache: penulisan; foto lama dibuang setelah yang baru tersimpan.
@router.post("/movements/{card_id}/proof", response_model=TabletStockMovementOut)
async def attach_proof(
    card_id: str,
    file: UploadFile = File(...),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(c.PROOF_GATE)),
):
    """Foto nota barang masuk atau bukti rusak; catatan penutupan periode dan stok awal tetap tertutup bagi tablet."""
    with _domain_errors():
        _tablet_card(db, device.outlet_id, card_id)
        image = await uploads.receive(file, ledger.PROOF_RULE)
        ledger.set_proof(db, device.outlet_id, card_id, image)
    return _one(db, card_id, public_base_url())


def _request_out(db: Session, request: IngredientCountRequest | None) -> TabletStockRequestOut | None:
    if request is None:
        return None
    names = user_names(db, [request.requested_by, request.decided_by])
    return TabletStockRequestOut(
        status=request.status,
        note=request.note,
        requested_by=names.get(request.requested_by or ""),
        created_at=request.created_at,
        decided_by=names.get(request.decided_by or ""),
        decided_at=request.decided_at,
    )


@router.get("/opening-period", response_model=TabletStockOpeningPeriodOut)
def opening_period(device: Device = Depends(tablet), db: Session = Depends(get_db), _: User = Depends(require_gate(c.PICK_GATE))):
    """Periode berjalan, berapa bahan yang stok awalnya sudah diisi, dan pengajuan tutup periode terakhirnya."""
    # Hitungan terisi satu sumber dengan web (ingredient_openings.fill_status).
    fill = openings.fill_status(db, device.outlet_id)
    start, total, filled = fill.start, fill.total, fill.filled
    # Rentang tutup dibaca dari satu aturan yang sama dengan web supaya tablet dan web menyebut periode yang sama.
    with _domain_errors():
        close_start, close_end = counts.closing_period(db, device.outlet_id)
    return TabletStockOpeningPeriodOut(start=start, close_start=close_start, close_end=close_end, filled=filled, total=total, request=_request_out(db, close_requests.shown(db, device.outlet_id, start)))


def _journey(db: Session, outlet_id: str, ingredient_id: str) -> TabletStockJourneyOut:
    start = openings.running_start(db, outlet_id)
    journey = openings.journey(db, outlet_id, ingredient_id, start)
    opening = openings.openings(db, outlet_id, start, [ingredient_id]).get(ingredient_id)
    by = user_names(db, [opening.user_id]).get(opening.user_id or "") if opening else None
    return TabletStockJourneyOut(
        start=journey.start,
        opening=journey.opening,
        opening_set=journey.opening_set,
        opening_by=by,
        opening_at=opening.written_at if opening else None,
        received=journey.received,
        sold=journey.sold,
        wasted=journey.wasted,
        trial=journey.trial,
        adjusted=journey.adjusted,
        stock=journey.stock,
    )


@router.get("/ingredients/{ingredient_id}/journey", response_model=TabletStockJourneyOut)
def ingredient_journey(ingredient_id: str, device: Device = Depends(tablet), db: Session = Depends(get_db), _: User = Depends(require_gate(c.HISTORY_GATE))):
    """Perjalanan stok satu bahan di periode berjalan: stok awal, masuk, penjualan, rusak, RnD, penyesuaian, dan stok sekarang."""
    with _domain_errors():
        return _journey(db, device.outlet_id, ingredient_id)


@router.put("/ingredients/{ingredient_id}/opening", response_model=TabletStockJourneyOut)
def set_opening(ingredient_id: str, body: TabletStockOpeningIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(c.PERMISSION_COUNT))):
    """Mengisi atau mengubah stok awal periode berjalan; selisihnya dicatat sebagai penyesuaian, bukan pembelian."""
    with _domain_errors():
        openings.write(db, user, device.outlet_id, ingredient_id, body.qty, openings.running_start(db, device.outlet_id))
        return _journey(db, device.outlet_id, ingredient_id)


@router.delete("/ingredients/{ingredient_id}/opening", response_model=TabletStockJourneyOut)
def remove_opening(ingredient_id: str, device: Device = Depends(tablet), db: Session = Depends(get_db), _: User = Depends(require_permission(c.PERMISSION_COUNT))):
    with _domain_errors():
        openings.remove(db, device.outlet_id, ingredient_id, openings.running_start(db, device.outlet_id))
        return _journey(db, device.outlet_id, ingredient_id)


@router.get("/ingredients/{ingredient_id}/recipes", response_model=TabletStockRecipeUsePageOut)
def ingredient_recipes(
    ingredient_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(c.DEFAULT_PAGE_SIZE, ge=1, le=c.MAX_PAGE_SIZE),
    device: Device = Depends(tablet),
    db: Session = Depends(get_db),
    _: User = Depends(require_gate(c.PICK_GATE)),
):
    """Menu yang resepnya di cabang ini memakai bahan itu, dengan takaran per porsi; tanpa biaya."""
    with _domain_errors():
        ledger.own_ingredient(db, device.outlet_id, ingredient_id)
    filters = [RecipeIngredient.ingredient_id == ingredient_id, RecipeIngredient.outlet_id == device.outlet_id]
    total = db.scalar(select(func.count()).select_from(RecipeIngredient).where(*filters)) or 0
    rows = db.execute(
        select(MenuItem.id, MenuItem.name, RecipeIngredient.qty)
        .join(MenuItem, MenuItem.id == RecipeIngredient.menu_item_id)
        .where(*filters)
        .order_by(MenuItem.name, MenuItem.id)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return TabletStockRecipeUsePageOut(items=[TabletStockRecipeUseOut(menu_item_id=row[0], menu_name=row[1], qty=row[2]) for row in rows], total=total, page=page, size=size)


@router.post("/close-requests", response_model=TabletStockRequestOut, status_code=status.HTTP_201_CREATED)
def request_close(body: TabletStockCloseRequestIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(require_permission(c.PERMISSION_CLOSE_PERIOD))):
    """Admin yang menutup periode di web; tablet hanya mengajukan."""
    with _domain_errors():
        request = close_requests.submit(db, user, device.outlet_id, body.note)
    return _request_out(db, request)


# Banyak bahan sekaligus lewat pintu massal bersama; setiap baris memakai aturan yang sama dengan isi satu bahan.
opening_bulk = APIRouter(prefix="/openings")
bulk.add_bulk_routes(
    opening_bulk,
    c.PERMISSION_COUNT,
    create_schema=TabletStockOpeningRowIn,
    create=lambda db, body, user, outlet_id: openings.write(db, user, outlet_id, body.ingredient_id, body.qty, openings.running_start(db, outlet_id)),
    create_context=tablet_outlet_id,
)
router.include_router(opening_bulk)
