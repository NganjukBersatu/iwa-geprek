"""The one door for recording and correcting expenses; the tablet records, the management web oversees, both obey these rules."""
import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.clock import now
from app.core.errors import DomainError
from app.core.finance import session_control
from app.core.finance.session_totals import refresh_closed
from app.core.storage import folders
from app.core.uploads import UploadedFile, UploadRule
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.expense import Expense, FundSource
from app.models.ingredient import Ingredient
from app.models.routine_item import RoutineItem
from app.models.user import User

PERMISSION_RECORD = "pengeluaran.catat"
PERMISSION_EDIT_ALL = "pengeluaran.ubah_semua"
PERMISSION_EDIT_OWN = "pengeluaran.ubah_sendiri"
PERMISSION_PICK_SESSION = "pengeluaran.pilih_shift"
PERMISSION_VIEW_ALL = "pengeluaran.lihat_semua"

RECEIPT_FOLDER = folders.RECEIPT
SHARED_RECEIPT_FOLDER = folders.SHARED_RECEIPT

BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404

EXPENSE_NOT_FOUND = "Pengeluaran tidak ditemukan."
SESSION_NOT_FOUND = "Sesi tidak ditemukan."
NO_PERMISSION = "Peran '{role}' tidak punya izin '{permission}'."
RECORDED_BY_OTHER = "Pengeluaran ini dicatat orang lain."
SESSION_CLOSED = "Sesinya sudah ditutup, pengeluaran ini tidak bisa diubah lagi."
PICK_RUNNING_SESSION = "Sesi itu sudah ditutup; pilih sesi yang sedang berjalan."
NO_OPEN_SESSION = "Buka sesi kasir dulu sebelum mencatat pengeluaran."
NEEDS_SESSION = "Pengeluaran dari omzet tunai atau uang belanja harus menempel ke sesi kasir yang sedang berjalan. Pilih sesinya, atau pakai sumber dana lain."
SHOPPING_FUND_OFF = "Uang belanja belum diaktifkan untuk cabang ini. Isi nominalnya di pengaturan cabang, lalu buka sesi baru."
NO_SESSION_FOR_SOURCE = "Pengeluaran ini tidak menempel ke sesi, jadi tidak bisa dari omzet tunai atau uang belanja."
ROUTINE_NAME_LOCKED = "Nama pembelian item rutin mengikuti katalognya; ubah di item rutin."
INGREDIENT_NOT_FOUND = "Bahan tidak ditemukan di cabang ini, atau sudah tidak aktif."
QUANTITY_NEEDS_INGREDIENT = "Jumlah hanya untuk baris bahan; pilih bahannya dulu."

SESSION_SOURCES = (FundSource.DRAWER_CASH, FundSource.SHOPPING_FUND)


@dataclass(frozen=True)
class ExpenseDraft:
    item_name: str
    amount: Decimal
    fund_source: FundSource
    note: str | None
    buyer: str | None
    session_id: str | None
    ingredient_id: str | None = None
    quantity: Decimal | None = None


@dataclass(frozen=True)
class ReceiptEntry:
    item_name: str
    amount: Decimal
    # Names one of the branch's ingredients; the price stays the receipt's and the stock is never touched.
    ingredient_id: str | None = None
    quantity: Decimal | None = None


@dataclass(frozen=True)
class ReceiptDraft:
    """One receipt: each entry becomes its own expense, sharing the fund source, buyer, note, session and photo."""

    entries: tuple[ReceiptEntry, ...]
    fund_source: FundSource
    note: str | None
    buyer: str | None
    session_id: str | None


def _tidy(text: str | None) -> str | None:
    cleaned = (text or "").strip()
    return cleaned or None


def _role(user: User) -> str:
    return user.role.name if user.role else "-"


def _target_session(db: Session, user: User, requested: str | None, source: FundSource) -> CashSession | None:
    """Without the pick permission it is always the person's own running session; with it, any running session, or none for other funds."""
    if not user.allows(PERMISSION_PICK_SESSION):
        own = session_control.running_of(db, user.id)
        if own is None:
            raise DomainError(NO_OPEN_SESSION)
        return own
    if requested:
        session = session_control.held(db, requested)
        if session is None:
            raise DomainError(SESSION_NOT_FOUND, status=NOT_FOUND)
        # Edit-all may add a forgotten purchase to a closed session; its frozen figures are worked out again on record.
        if session.status != CashSessionStatus.OPEN and not user.allows(PERMISSION_EDIT_ALL):
            raise DomainError(PICK_RUNNING_SESSION)
        return session
    own = session_control.running_of(db, user.id)
    if own is not None:
        return own
    if source in SESSION_SOURCES:
        raise DomainError(NEEDS_SESSION)
    return None


def _check_shopping_fund(session: CashSession | None, source: FundSource) -> None:
    """The shopping fund exists only in sessions opened with the three money parts; elsewhere no reconciliation would count it."""
    if source == FundSource.SHOPPING_FUND and (session is None or session.planned_shopping is None):
        raise DomainError(SHOPPING_FUND_OFF)


def read(db: Session, user: User, expense_id: str) -> None:
    """Checks that this person may open the expense; another branch's, or someone else's without view-all, answers as missing."""
    expense = db.get(Expense, expense_id)
    if expense is None or (user.locked_outlet_id and expense.outlet_id != user.locked_outlet_id):
        raise DomainError(EXPENSE_NOT_FOUND, status=NOT_FOUND)
    if not user.allows(PERMISSION_VIEW_ALL) and expense.cashier_id != user.id:
        raise DomainError(EXPENSE_NOT_FOUND, status=NOT_FOUND)


def _editable(db: Session, user: User, expense_id: str, permission_for_own: str) -> Expense:
    """Anyone with edit-all may correct anything; otherwise only one's own, and only while its session runs, since a closed session's difference is already signed off."""
    expense = db.get(Expense, expense_id)
    # Another branch's expense answers as missing, even for someone who may edit every expense of their own branch.
    if expense is None or (user.locked_outlet_id and expense.outlet_id != user.locked_outlet_id):
        raise DomainError(EXPENSE_NOT_FOUND, status=NOT_FOUND)
    if user.allows(PERMISSION_EDIT_ALL):
        return expense
    if not user.allows(permission_for_own):
        raise DomainError(NO_PERMISSION.format(role=_role(user), permission=permission_for_own), status=FORBIDDEN)
    if expense.cashier_id != user.id:
        raise DomainError(RECORDED_BY_OTHER, status=FORBIDDEN)
    session = db.get(CashSession, expense.cash_session_id) if expense.cash_session_id else None
    if session is not None and session.status == CashSessionStatus.CLOSED:
        raise DomainError(SESSION_CLOSED)
    return expense


def _after_change(db: Session, session_id: str | None, routine_item_id: str | None) -> None:
    """A closed session's frozen figures and a routine item's due date both follow the expenses still on record."""
    if session_id:
        session = db.get(CashSession, session_id)
        if session is not None:
            refresh_closed(db, session)
    if routine_item_id:
        item = db.get(RoutineItem, routine_item_id)
        if item is not None:
            db.flush()
            last = db.execute(
                select(Expense.business_day, Expense.created_at)
                .where(Expense.routine_item_id == item.id)
                .order_by(Expense.business_day.desc(), Expense.created_at.desc())
                .limit(1)
            ).first()
            item.last_purchased_at = last.created_at if last else None
            item.next_due_date = last.business_day + timedelta(days=item.cycle_days) if last else None


def _ingredient(db: Session, outlet_id: str, ingredient_id: str) -> Ingredient:
    """Only an active ingredient of the expense's own branch; one is never created from here."""
    ingredient = db.get(Ingredient, ingredient_id)
    if ingredient is None or ingredient.outlet_id != outlet_id or not ingredient.is_active:
        raise DomainError(INGREDIENT_NOT_FOUND)
    return ingredient


def _new_expense(
    db: Session,
    user: User,
    outlet_id: str,
    session: CashSession | None,
    entry: ReceiptEntry,
    source: FundSource,
    note: str | None,
    buyer: str | None,
    receipt_path: str | None,
) -> Expense:
    # A session's drawer never mixes branches; an expense without a session belongs to the writer's branch.
    branch = session.outlet_id if session else outlet_id
    if entry.quantity is not None and entry.ingredient_id is None:
        raise DomainError(QUANTITY_NEEDS_INGREDIENT)
    ingredient = _ingredient(db, branch, entry.ingredient_id) if entry.ingredient_id else None
    return Expense(
        id=str(uuid.uuid4()),
        outlet_id=branch,
        cash_session_id=session.id if session else None,
        cashier_id=user.id,
        routine_item_id=None,
        item_name=entry.item_name.strip(),
        amount=entry.amount,
        fund_source=source,
        note=_tidy(note),
        buyer=_tidy(buyer),
        receipt_path=receipt_path,
        ingredient_id=ingredient.id if ingredient else None,
        quantity=entry.quantity if ingredient else None,
        unit_id=ingredient.unit_id if ingredient else None,
        created_at=now(),
    )


def _discard_unshared(db: Session, path: str | None) -> None:
    """One receipt photo may back several expenses; the file goes only with the last of them. Call after the commit."""
    if path and db.scalar(select(Expense.id).where(Expense.receipt_path == path).limit(1)) is None:
        uploads.discard(db, path)


def record(db: Session, user: User, outlet_id: str, draft: ExpenseDraft) -> Expense:
    session = _target_session(db, user, draft.session_id, draft.fund_source)
    _check_shopping_fund(session, draft.fund_source)
    entry = ReceiptEntry(item_name=draft.item_name, amount=draft.amount, ingredient_id=draft.ingredient_id, quantity=draft.quantity)
    expense = _new_expense(db, user, outlet_id, session, entry, draft.fund_source, draft.note, draft.buyer, None)
    db.add(expense)
    _after_change(db, expense.cash_session_id, None)
    db.commit()
    db.refresh(expense)
    return expense


def record_receipt(db: Session, user: User, outlet_id: str, draft: ReceiptDraft, image: UploadedFile | None, rule: UploadRule) -> list[Expense]:
    """All entries are saved together or not at all, pointing at one stored photo."""
    session = _target_session(db, user, draft.session_id, draft.fund_source)
    _check_shopping_fund(session, draft.fund_source)
    path = f"{RECEIPT_FOLDER}/{SHARED_RECEIPT_FOLDER}/{uuid.uuid4()}{image.extension}" if image else None
    recorded = [
        _new_expense(db, user, outlet_id, session, entry, draft.fund_source, draft.note, draft.buyer, path) for entry in draft.entries
    ]
    db.add_all(recorded)
    _after_change(db, session.id if session else None, None)
    if image is not None and path is not None:
        uploads.store(db, path, image, rule)
    db.commit()
    return recorded


def update(db: Session, user: User, expense_id: str, changes: dict) -> Expense:
    expense = _editable(db, user, expense_id, PERMISSION_EDIT_OWN)
    if "item_name" in changes and changes["item_name"] is not None:
        if expense.routine_item_id:
            raise DomainError(ROUTINE_NAME_LOCKED)
        expense.item_name = changes["item_name"].strip()
    if "amount" in changes and changes["amount"] is not None:
        expense.amount = changes["amount"]
    if "fund_source" in changes and changes["fund_source"] is not None:
        source = changes["fund_source"]
        if source in SESSION_SOURCES and expense.cash_session_id is None:
            raise DomainError(NO_SESSION_FOR_SOURCE)
        if source == FundSource.SHOPPING_FUND:
            _check_shopping_fund(db.get(CashSession, expense.cash_session_id), source)
        expense.fund_source = source
    if "note" in changes:
        expense.note = _tidy(changes["note"])
    if "buyer" in changes:
        expense.buyer = _tidy(changes["buyer"])
    if "ingredient_id" in changes:
        ingredient_id = changes["ingredient_id"]
        if ingredient_id is None:
            expense.ingredient_id = expense.quantity = expense.unit_id = None
        elif ingredient_id != expense.ingredient_id:
            ingredient = _ingredient(db, expense.outlet_id, ingredient_id)
            expense.ingredient_id, expense.unit_id = ingredient.id, ingredient.unit_id
    if "quantity" in changes:
        if changes["quantity"] is not None and expense.ingredient_id is None:
            raise DomainError(QUANTITY_NEEDS_INGREDIENT)
        expense.quantity = changes["quantity"]
    _after_change(db, expense.cash_session_id, None)
    db.commit()
    db.refresh(expense)
    return expense


def delete(db: Session, user: User, expense_id: str) -> None:
    expense = _editable(db, user, expense_id, PERMISSION_EDIT_OWN)
    session_id, routine_item_id, receipt = expense.cash_session_id, expense.routine_item_id, expense.receipt_path
    db.delete(expense)
    _after_change(db, session_id, routine_item_id)
    db.commit()
    _discard_unshared(db, receipt)


def set_receipt(db: Session, user: User, expense_id: str, image: UploadedFile, rule: UploadRule) -> Expense:
    """Attaching the receipt is part of recording, so recording is enough for one's own; the other limits stay."""
    expense = _editable(db, user, expense_id, PERMISSION_RECORD)
    path = f"{RECEIPT_FOLDER}/{expense.id}/{uuid.uuid4()}{image.extension}"
    uploads.store(db, path, image, rule)
    previous = expense.receipt_path
    expense.receipt_path = path
    db.commit()
    db.refresh(expense)
    _discard_unshared(db, previous)
    return expense
