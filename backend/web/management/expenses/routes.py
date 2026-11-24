"""HTTP surface of the expense screen; every rule lives in app.core.finance.expenses."""
import asyncio
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import bulk, cache, page_cursor, receipts, uploads
from app.core.auth import current_user, readable_outlet_id, require_permission, writable_outlet_id
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.core.finance import expense_choices, expense_reads, expenses
from app.core.finance.expense_schemas import BuyerChoiceOut, ExpenseCreateIn, ExpenseOut, ExpensePageOut, ExpenseUpdateIn, IngredientChoiceOut, expense_draft, expense_out, receipt_draft
from app.core.http import public_base_url
from app.core.receipts import ingredients as receipt_ingredients
from app.core.receipts.schemas import ReceiptReadingOut, reading_out
from app.core.receipts.upload import RULE
from app.models.expense import FundSource
from app.models.user import User
from web.management.expenses import repository
from web.management.expenses.mappers import session_choice_out
from web.management.expenses.schemas import SessionChoiceOut, SessionChoicePageOut
from web.management.reports.common import month_to_date, resolve_range

router = APIRouter(prefix="/expenses", tags=["web-expenses"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_SEARCH_LENGTH = 100
DEFAULT_CHOICE_SIZE = 30

PAGE = TypeAdapter(ExpensePageOut)
CHOICES = TypeAdapter(list[SessionChoiceOut])
CHOICE_PAGE = TypeAdapter(SessionChoicePageOut)


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
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    fund_source: FundSource | None = Query(None),
    session_id: str | None = Query(None, description="Only this cash session's expenses, whatever the dates"),
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the item name or note"),
    sort: Sort = None,
    page: int = Query(1, ge=1),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Without view-all a person sees only what they recorded, whatever the request asks."""
    with _domain_errors():
        first, last = month_to_date(start, end)
    cashier_id = None if user.allows(expenses.PERMISSION_VIEW_ALL) else user.id
    term = (search or "").strip() or None
    base_url = public_base_url()

    def build() -> ExpensePageOut:
        rows, total, total_amount, drawer_amount = expense_reads.page_of(db, first, last, outlet_id, cashier_id, fund_source, term, sort, page, size, session_id)
        return ExpensePageOut(
            start=first,
            end=last,
            items=[expense_out(row, base_url) for row in rows],
            total=total,
            page=page,
            size=size,
            total_amount=total_amount,
            drawer_amount=drawer_amount,
        )

    with _domain_errors():
        # Free text has no end of values, so it is never a key.
        if term:
            return build()
        return cache.read(
            "web.expenses",
            (first, last, outlet_id, cashier_id, fund_source, session_id, sort, page, size, base_url),
            build,
            PAGE,
            cache.LIST_SECONDS,
        )


@router.get("/sessions/page", response_model=SessionChoicePageOut)
def session_choice_page(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the cashier name or shift code"),
    size: int = Query(DEFAULT_CHOICE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = Query(None, max_length=page_cursor.MAX_CURSOR_LENGTH, description="next_cursor of the previous page"),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(expenses.PERMISSION_PICK_SESSION)),
):
    """Sessions an expense may be attached to, a page at a time while the list scrolls; closed ones only for those who may edit every expense."""
    with _domain_errors():
        first, last = resolve_range(start, end) if start or end else (None, None)
    term = (search or "").strip() or None
    edits_all = user.allows(expenses.PERMISSION_EDIT_ALL)
    scope = f"expense-sessions:{outlet_id}:{first}:{last}:{term}:{edits_all}:{size}"

    def build() -> SessionChoicePageOut:
        with _domain_errors():
            rows, next_cursor = repository.session_choice_page(db, outlet_id, first, last, term, edits_all, size, scope, cursor)
        return SessionChoicePageOut(items=[session_choice_out(session, username) for session, username in rows], next_cursor=next_cursor)

    # Hanya halaman pertama tanpa kata cari yang disimpan: teks bebas dan kursor tidak punya batas nilai.
    if term or cursor:
        return build()
    return cache.read("web.expenses.sessions.page", (outlet_id, first, last, edits_all, size), build, CHOICE_PAGE, cache.LIST_SECONDS)


# Usang sejak 8 Nov 2026: hanya untuk tab web yang dibuka sebelum deploy; hapus pada rilis berikutnya bersama CHOICES.
@router.get("/sessions", response_model=list[SessionChoiceOut])
def session_choices(
    start: Day | None = Query(None),
    end: Day | None = Query(None),
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the cashier name or shift code"),
    size: int = Query(DEFAULT_CHOICE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(expenses.PERMISSION_PICK_SESSION)),
):
    """Sessions an expense may be attached to: running ones, plus closed ones for those who may edit every expense."""
    with _domain_errors():
        first, last = resolve_range(start, end) if start or end else (None, None)
    term = (search or "").strip() or None
    edits_all = user.allows(expenses.PERMISSION_EDIT_ALL)

    def build() -> list[SessionChoiceOut]:
        return [session_choice_out(session, username) for session, username in repository.session_choices(db, outlet_id, first, last, term, edits_all, size)]

    # Free text has no end of values, so it is never a key.
    if term:
        return build()
    return cache.read("web.expenses.sessions", (outlet_id, first, last, edits_all, size), build, CHOICES, cache.LIST_SECONDS)


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    body: ExpenseCreateIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(expenses.PERMISSION_RECORD)),
):
    with _domain_errors():
        expense = expenses.record(db, user, outlet_id, expense_draft(body))
    return _out(db, expense.id, public_base_url())


@router.get("/ingredients", response_model=list[IngredientChoiceOut])
def ingredient_choices(
    search: str | None = Query(None, max_length=MAX_SEARCH_LENGTH, description="Part of the ingredient name"),
    size: int = Query(DEFAULT_CHOICE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    page: int = Query(1, ge=1, description="Asked for while the list scrolls; a page shorter than size is the end"),
    outlet_id: str = Depends(writable_outlet_id),
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
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(expenses.PERMISSION_RECORD)),
):
    """Only reads the photo to fill the form; nothing is stored until the receipt is saved. Lines are matched against the branch's own ingredients, never added to them."""
    with _domain_errors():
        image = await uploads.receive(file, RULE)
        reading = await asyncio.to_thread(receipts.read, image.content)
    return reading_out(reading, receipt_ingredients.match(db, outlet_id, [line.name for line in reading.items]))


@router.post("/receipts", response_model=list[ExpenseOut], status_code=status.HTTP_201_CREATED)
async def record_receipt(
    data: str = Form(..., description="ExpenseReceiptIn as JSON"),
    file: UploadFile | None = File(None),
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(expenses.PERMISSION_RECORD)),
):
    draft = receipt_draft(data)
    with _domain_errors():
        image = await uploads.receive(file, RULE, required=False)
        recorded = expenses.record_receipt(db, user, outlet_id, draft, image, RULE)
    base_url = public_base_url()
    return [expense_out(row, base_url) for row in expense_reads.many_with_context(db, [item.id for item in recorded])]


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    with _domain_errors():
        expenses.read(db, user, expense_id)
    return _out(db, expense_id, public_base_url())


@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: str,
    body: ExpenseUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    with _domain_errors():
        expenses.update(db, user, expense_id, body.model_dump(exclude_unset=True))
    return _out(db, expense_id, public_base_url())


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    with _domain_errors():
        expenses.delete(db, user, expense_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{expense_id}/receipt", response_model=ExpenseOut)
async def replace_receipt(
    expense_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    with _domain_errors():
        image = await uploads.receive(file, RULE)
        expenses.set_receipt(db, user, expense_id, image, RULE)
    return _out(db, expense_id, public_base_url())


bulk.add_bulk_routes(
    router,
    expenses.PERMISSION_RECORD,
    create_schema=ExpenseCreateIn,
    create=lambda db, body, user, outlet_id: expenses.record(db, user, outlet_id, expense_draft(body)),
    create_context=writable_outlet_id,
    update_schema=ExpenseUpdateIn,
    update=lambda db, expense_id, body, user: expenses.update(db, user, expense_id, body.model_dump(exclude_unset=True)),
    delete=lambda db, expense_id, user: expenses.delete(db, user, expense_id),
)
