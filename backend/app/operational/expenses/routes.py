"""Expenses on the tablet; the rules live in app.core.finance.expenses and the receipt reading in app.core.receipts."""
import asyncio
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core import receipts, uploads
from app.core.auth import current_user, require_permission
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.core.finance import deposited, expense_choices, expense_reads, expenses
from app.core.finance.deposited import DayStateOut, DayStatesIn
from app.core.finance.expense_schemas import BuyerChoiceOut, ExpenseOut, ExpensePageOut, ExpenseUpdateIn, IngredientChoiceOut, expense_out, receipt_draft
from app.core.http import public_base_url
from app.core.receipts import ingredients as receipt_ingredients
from app.core.receipts.schemas import ReceiptReadingOut, reading_out
from app.core.receipts.upload import RULE
from app.models.expense import FundSource
from app.models.user import User
from app.operational.device import tablet_outlet_id

router = APIRouter(prefix="/expenses", tags=["v2-operational-expenses"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_SEARCH_LENGTH = 100
DEFAULT_CHOICE_SIZE = 30
RANGE_REVERSED = "Tanggal awal harus sebelum tanggal akhir."


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _out(db: Session, expense_id: str, base_url: str) -> ExpenseOut:
    return expense_out(expense_reads.with_context(db, expense_id), base_url)


@router.get("", response_model=ExpensePageOut)
def list_expenses(
    start: Day = Query(...),
    end: Day = Query(...),
    fund_source: FundSource | None = Query(None),
    user_id: str | None = Query(None, max_length=64, description="Only narrows the list for a person with view-all; others always see only their own"),
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the item name or note"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str = Depends(tablet_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Without view-all a person sees only what they recorded, whatever the request asks."""
    if start > end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=RANGE_REVERSED)
    recorder_id = user_id if user.allows(expenses.PERMISSION_VIEW_ALL) else user.id
    with _domain_errors():
        rows, total, total_amount, drawer_amount = expense_reads.page_of(db, start, end, outlet_id, recorder_id, fund_source, (search or "").strip() or None, sort, page, size)
    base_url = public_base_url()
    return ExpensePageOut(
        start=start,
        end=end,
        items=[expense_out(row, base_url) for row in rows],
        total=total,
        page=page,
        size=size,
        total_amount=total_amount,
        drawer_amount=drawer_amount,
    )


@router.get("/ingredients", response_model=list[IngredientChoiceOut])
def ingredient_choices(
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the ingredient name"),
    size: int = Query(DEFAULT_CHOICE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    page: int = Query(1, ge=1, description="Asked for while the list scrolls; a page shorter than size is the end"),
    outlet_id: str = Depends(tablet_outlet_id),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(expenses.PERMISSION_RECORD)),
):
    """The branch's active ingredients a line may name; picking one never changes its stock."""
    rows = expense_choices.ingredients(db, outlet_id, (search or "").strip() or None, size, page)
    return [IngredientChoiceOut(id=row.id, name=row.name, unit_id=row.unit_id, unit_name=row.unit_name) for row in rows]


@router.get("/buyers", response_model=list[BuyerChoiceOut])
def buyer_choices(
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the employee's name or username"),
    size: int = Query(DEFAULT_CHOICE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    page: int = Query(1, ge=1, description="Asked for while the list scrolls; a page shorter than size is the end"),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(expenses.PERMISSION_RECORD)),
):
    """Every active employee, from any branch; the expense keeps the chosen name."""
    rows = expense_choices.buyers(db, (search or "").strip() or None, size, page)
    return [BuyerChoiceOut(id=row.id, name=row.name, outlet_name=row.outlet_name) for row in rows]


@router.post("/receipts/read", response_model=ReceiptReadingOut)
async def read_receipt(
    file: UploadFile = File(...),
    outlet_id: str = Depends(tablet_outlet_id),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(expenses.PERMISSION_RECORD)),
):
    """Only reads the photo to fill the form; nothing is stored until the expense is saved. Lines are matched against the branch's own ingredients, never added to them."""
    with _domain_errors():
        image = await uploads.receive(file, RULE)
        reading = await asyncio.to_thread(receipts.read, image.content)
    return reading_out(reading, receipt_ingredients.match(db, outlet_id, [line.name for line in reading.items]))


@router.post("/receipts", response_model=list[ExpenseOut], status_code=status.HTTP_201_CREATED)
async def record_receipt(
    data: str = Form(..., description="ExpenseReceiptIn as JSON"),
    file: UploadFile | None = File(None),
    outlet_id: str = Depends(tablet_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(expenses.PERMISSION_RECORD)),
):
    """Every new expense comes through here, one line or a whole receipt, so its photo is stored once."""
    draft = receipt_draft(data)
    with _domain_errors():
        image = await uploads.receive(file, RULE, required=False)
        recorded = expenses.record_receipt(db, user, outlet_id, draft, image, RULE)
    base_url = public_base_url()
    return [expense_out(row, base_url) for row in expense_reads.many_with_context(db, [item.id for item in recorded])]


# Not cached: it is read right before changing money, so it must be what the database holds now.
@router.post("/day-states", response_model=list[DayStateOut])
def day_states(
    body: DayStatesIn,
    outlet_id: str = Depends(tablet_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Whether the days of the expenses about to change were handed over already or still have a session running."""
    return deposited.day_states(db, body, outlet_id, user.id)


@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: str, body: ExpenseUpdateIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    with _domain_errors():
        expenses.update(db, user, expense_id, body.model_dump(exclude_unset=True))
    return _out(db, expense_id, public_base_url())


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    with _domain_errors():
        expenses.delete(db, user, expense_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{expense_id}/receipt", response_model=ExpenseOut)
async def replace_receipt(expense_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(current_user)):
    with _domain_errors():
        image = await uploads.receive(file, RULE)
        expenses.set_receipt(db, user, expense_id, image, RULE)
    return _out(db, expense_id, public_base_url())
