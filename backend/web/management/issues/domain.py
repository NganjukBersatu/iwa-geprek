"""What a detector finds and what every detector is handed."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum

from sqlalchemy.orm import Session

from app.core.date_range import range_start


class IssueLevel(str, Enum):
    """Problem stops work or loses money now; warning will become one; notice is only to know; suggestion tidies data."""

    PROBLEM = "problem"
    WARNING = "warning"
    NOTICE = "notice"
    SUGGESTION = "suggestion"


LEVEL_ORDER = {IssueLevel.PROBLEM: 0, IssueLevel.WARNING: 1, IssueLevel.NOTICE: 2, IssueLevel.SUGGESTION: 3}


class IssueKind(str, Enum):
    EXPENSE_OVER_INCOME = "expense_over_income"
    DRAWER_OVER_CASH = "drawer_over_cash"
    CASH_DIFFERENCE = "cash_difference"
    FLOAT_DIFFERENCE = "float_difference"
    SHOPPING_DIFFERENCE = "shopping_difference"
    SESSION_LEFT_OPEN = "session_left_open"
    DEPOSIT_HELD = "deposit_held"
    NON_CASH_UNCHECKED = "non_cash_unchecked"
    NON_CASH_MISMATCH = "non_cash_mismatch"
    OVERPAYMENT = "overpayment"
    VOIDS_MANY = "voids_many"
    CANCELLATION_WAITING = "cancellation_waiting"
    ORDER_OFF_BOARD = "order_off_board"
    STOCK_OUT = "stock_out"
    STOCK_NEGATIVE = "stock_negative"
    STOCK_LOW = "stock_low"
    COUNT_OVER_TOLERANCE = "count_over_tolerance"
    COUNT_REQUEST_WAITING = "count_request_waiting"
    OPENING_MISSING = "opening_missing"
    PURCHASE_PRICE_JUMP = "purchase_price_jump"
    INGREDIENT_IDLE = "ingredient_idle"
    INGREDIENT_NO_MINIMUM = "ingredient_no_minimum"
    INGREDIENT_UNUSED = "ingredient_unused"
    MARGIN_BELOW_TARGET = "margin_below_target"
    MENU_WITHOUT_RECIPE = "menu_without_recipe"
    MENU_SHOULD_BE_VARIANT = "menu_should_be_variant"
    MENU_UNSOLD = "menu_unsold"
    PROMO_ENDING = "promo_ending"
    PROMO_UNUSED = "promo_unused"
    LEAVE_WAITING = "leave_waiting"
    USER_UNSCHEDULED = "user_unscheduled"
    BRANCH_WITHOUT_USERS = "branch_without_users"
    NO_CLOCK_IN = "no_clock_in"
    NO_CLOCK_OUT = "no_clock_out"
    AUTO_CLOSED = "auto_closed"
    LATE_REPEATED = "late_repeated"
    OVERTIME_OPEN = "overtime_open"
    USER_UNPLACED = "user_unplaced"
    TASK_MISSED = "task_missed"
    DEVICE_IDLE = "device_idle"
    DEVICE_CODE_EXPIRED = "device_code_expired"


@dataclass(frozen=True)
class Issue:
    """The figures each kind fills are listed next to its detector; `compared` is what `amount` or `percent` is held against."""

    kind: IssueKind
    level: IssueLevel
    outlet_id: str | None
    subject_id: str | None
    subject: str
    # What the subject is when one kind covers several things, such as an ingredient or a resold item.
    subject_kind: str | None = None
    day: date | None = None
    at: datetime | None = None
    amount: Decimal | None = None
    compared: Decimal | None = None
    percent: Decimal | None = None
    unit: str | None = None
    count: int | None = None
    days: Decimal | None = None


@dataclass(frozen=True)
class Scope:
    """`outlet_id` is the branch asked for, None for every branch; `outlet_ids` are the active branches that covers."""

    db: Session
    outlet_id: str | None
    outlet_ids: list[str]
    today: date
    now: datetime

    @property
    def every_branch(self) -> bool:
        return self.outlet_id is None

    def first_day(self, days: int) -> date:
        """The first of the last `days` calendar days, today counted as one."""
        return self.today - timedelta(days=days - 1)

    def since(self, days: int) -> datetime:
        return range_start(self.first_day(days))
