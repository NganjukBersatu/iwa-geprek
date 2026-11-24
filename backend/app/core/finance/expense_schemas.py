"""Expense shapes shared by the tablet and the management web, so both send and receive exactly the same thing."""
from datetime import date, datetime
from decimal import Decimal

from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError

from app.core.finance.expense_reads import ExpenseRow
from app.core.finance.expenses import ExpenseDraft, ReceiptDraft, ReceiptEntry
from app.core.http import static_url
from app.models.cash_session import CashSessionStatus
from app.models.expense import FundSource

MAX_ITEM_NAME_LENGTH = 255
MAX_BUYER_LENGTH = 120
MAX_NOTE_LENGTH = 1000
MAX_RECEIPT_ITEMS = 100
QUANTITY_DIGITS = 12
QUANTITY_DECIMALS = 3


class ExpenseCreateIn(BaseModel):
    item_name: str = Field(min_length=1, max_length=MAX_ITEM_NAME_LENGTH)
    amount: Decimal = Field(gt=0)
    fund_source: FundSource
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)
    # Empty means the person recording it did the shopping.
    buyer: str | None = Field(None, max_length=MAX_BUYER_LENGTH)
    # Read only with the pick-session permission; everyone else is held to their own running session.
    session_id: str | None = None
    ingredient_id: str | None = None
    quantity: Decimal | None = Field(None, gt=0, max_digits=QUANTITY_DIGITS, decimal_places=QUANTITY_DECIMALS)


class ReceiptItemIn(BaseModel):
    item_name: str = Field(min_length=1, max_length=MAX_ITEM_NAME_LENGTH)
    amount: Decimal = Field(gt=0)
    # A line that names one of the branch's ingredients; the unit always follows the ingredient.
    ingredient_id: str | None = None
    quantity: Decimal | None = Field(None, gt=0, max_digits=QUANTITY_DIGITS, decimal_places=QUANTITY_DECIMALS)


class ExpenseReceiptIn(BaseModel):
    """One receipt: each item becomes its own expense, sharing the fund source, buyer, note, session and photo."""

    items: list[ReceiptItemIn] = Field(min_length=1, max_length=MAX_RECEIPT_ITEMS)
    fund_source: FundSource
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)
    buyer: str | None = Field(None, max_length=MAX_BUYER_LENGTH)
    session_id: str | None = None


class ExpenseUpdateIn(BaseModel):
    """Session, recorder and routine item are left out, so an expense can never be moved to another drawer."""

    item_name: str | None = Field(None, min_length=1, max_length=MAX_ITEM_NAME_LENGTH)
    amount: Decimal | None = Field(None, gt=0)
    fund_source: FundSource | None = None
    note: str | None = Field(None, max_length=MAX_NOTE_LENGTH)
    buyer: str | None = Field(None, max_length=MAX_BUYER_LENGTH)
    # Sending null turns the line back into a plain one, dropping its quantity too.
    ingredient_id: str | None = None
    quantity: Decimal | None = Field(None, gt=0, max_digits=QUANTITY_DIGITS, decimal_places=QUANTITY_DECIMALS)


class ExpenseOut(BaseModel):
    id: str
    outlet_id: str
    business_day: date
    outlet_name: str | None
    session_id: str | None
    session_closed: bool
    cashier_id: str
    cashier_username: str | None
    routine_item_id: str | None
    item_name: str
    amount: Decimal
    fund_source: FundSource
    note: str | None
    buyer: str | None
    receipt_url: str | None
    ingredient_id: str | None
    ingredient_name: str | None
    quantity: Decimal | None
    unit_name: str | None
    created_at: datetime


class IngredientChoiceOut(BaseModel):
    id: str
    name: str
    unit_id: str | None
    unit_name: str | None


class BuyerChoiceOut(BaseModel):
    id: str
    name: str
    outlet_name: str | None


class ExpensePageOut(BaseModel):
    start: date
    end: date
    items: list[ExpenseOut]
    total: int
    page: int
    size: int
    total_amount: Decimal
    drawer_amount: Decimal


def expense_out(row: ExpenseRow, base_url: str) -> ExpenseOut:
    expense = row.expense
    return ExpenseOut(
        id=expense.id,
        outlet_id=expense.outlet_id,
        business_day=expense.business_day,
        outlet_name=row.outlet_name,
        session_id=expense.cash_session_id,
        session_closed=row.session_status == CashSessionStatus.CLOSED,
        cashier_id=expense.cashier_id,
        cashier_username=row.username,
        routine_item_id=expense.routine_item_id,
        item_name=expense.item_name,
        amount=expense.amount,
        fund_source=expense.fund_source,
        note=expense.note,
        buyer=expense.buyer,
        receipt_url=static_url(base_url, expense.receipt_path),
        ingredient_id=expense.ingredient_id,
        ingredient_name=row.ingredient_name,
        quantity=expense.quantity,
        unit_name=row.unit_name,
        created_at=expense.created_at,
    )


def expense_draft(body: ExpenseCreateIn) -> ExpenseDraft:
    return ExpenseDraft(
        item_name=body.item_name,
        amount=body.amount,
        fund_source=body.fund_source,
        note=body.note,
        buyer=body.buyer,
        session_id=body.session_id,
        ingredient_id=body.ingredient_id,
        quantity=body.quantity,
    )


def receipt_draft(data: str) -> ReceiptDraft:
    """The receipt travels as a JSON form field next to its photo, so it is validated here instead of by the route signature."""
    try:
        body = ExpenseReceiptIn.model_validate_json(data)
    except ValidationError as error:
        raise RequestValidationError(error.errors()) from error
    return ReceiptDraft(
        entries=tuple(ReceiptEntry(item_name=item.item_name, amount=item.amount, ingredient_id=item.ingredient_id, quantity=item.quantity) for item in body.items),
        fund_source=body.fund_source,
        note=body.note,
        buyer=body.buyer,
        session_id=body.session_id,
    )
