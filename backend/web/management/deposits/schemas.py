from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from web.management.deposits import constants as c

Status = Literal["belum", "sebagian", "lunas"]
# Sorting by status goes from nothing handed over to settled.
STATUS_ORDER: tuple[Status, ...] = ("belum", "sebagian", "lunas")


class DepositIn(BaseModel):
    """Cash handed over on one date; [days] are the income days it settles, oldest first until the amount runs out."""

    deposit_date: date
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    note: str | None = Field(None, max_length=c.MAX_NOTE_LENGTH)
    days: list[date] = Field(min_length=1, max_length=c.MAX_DAYS)


class DepositNoteIn(BaseModel):
    note: str | None = Field(None, max_length=c.MAX_NOTE_LENGTH)


class DepositDayShareOut(BaseModel):
    day: date
    amount: Decimal


class DepositOut(BaseModel):
    id: str
    outlet_id: str
    outlet_name: str
    deposit_date: date
    amount: Decimal
    note: str | None
    photo_url: str | None
    user_name: str | None
    days: list[DepositDayShareOut]
    created_at: datetime


class DepositDayStateOut(BaseModel):
    day: date
    due: Decimal = Field(description="The cash profit of the day: what has to be handed over")
    paid: Decimal
    left: Decimal = Field(description="What is still held; zero once the day is settled")
    status: Status


class DepositSummaryOut(BaseModel):
    held: Decimal
    oldest_open_day: date | None
    paid_total: Decimal
    deposit_count: int
    last_deposit_date: date | None
    without_photo: int = Field(description="Deposits in the range that have no photo of the receipt")


class DepositDaysOut(BaseModel):
    start: date
    end: date
    items: list[DepositDayStateOut]
    # The days still held, in the order the table asked for, while `items` keeps every day by date.
    open: list[DepositDayStateOut]
    summary: DepositSummaryOut
