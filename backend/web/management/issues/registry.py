"""Every detector, the kinds it finds, and the permission that shows each kind: a new kind of issue is one line here and one detector."""
from collections.abc import Callable
from dataclasses import dataclass

from app.core.auth import FULL_ACCESS_ONLY, Gate
from app.core.orders.station_setup import PERMISSION_MANAGE as PERMISSION_STATIONS
from web.management.reports import gates as report_gates
from web.management.issues import constants as c
from web.management.issues.detectors import branch, menu, money, people, stations, stock
from web.management.issues.domain import Issue, IssueKind, Scope


@dataclass(frozen=True)
class Detector:
    run: Callable[[Scope], list[Issue]]
    kinds: tuple[IssueKind, ...]


# A kind is shown only to someone who may already see the data it comes from, so the page needs no permission of its own.
PERMISSION_OF: dict[IssueKind, Gate] = {
    IssueKind.EXPENSE_OVER_INCOME: report_gates.OVERVIEW,
    IssueKind.DRAWER_OVER_CASH: c.PERMISSION_SESSIONS,
    IssueKind.CASH_DIFFERENCE: c.PERMISSION_SESSIONS,
    IssueKind.FLOAT_DIFFERENCE: c.PERMISSION_SESSIONS,
    IssueKind.SHOPPING_DIFFERENCE: c.PERMISSION_SESSIONS,
    IssueKind.SESSION_LEFT_OPEN: c.PERMISSION_SESSIONS,
    IssueKind.DEPOSIT_HELD: c.PERMISSION_DEPOSITS,
    IssueKind.NON_CASH_UNCHECKED: report_gates.OVERVIEW,
    IssueKind.NON_CASH_MISMATCH: report_gates.OVERVIEW,
    # Kept to full access with its page until the owner gives overpayments a permission.
    IssueKind.OVERPAYMENT: FULL_ACCESS_ONLY,
    IssueKind.VOIDS_MANY: report_gates.VOIDS,
    IssueKind.CANCELLATION_WAITING: c.PERMISSION_APPROVE_VOID,
    IssueKind.ORDER_OFF_BOARD: PERMISSION_STATIONS,
    IssueKind.STOCK_OUT: c.PERMISSION_STOCK,
    IssueKind.STOCK_NEGATIVE: c.PERMISSION_STOCK,
    IssueKind.STOCK_LOW: c.PERMISSION_STOCK,
    IssueKind.COUNT_OVER_TOLERANCE: c.PERMISSION_STOCK,
    IssueKind.COUNT_REQUEST_WAITING: c.PERMISSION_STOCK,
    IssueKind.OPENING_MISSING: c.PERMISSION_STOCK,
    IssueKind.PURCHASE_PRICE_JUMP: c.PERMISSION_STOCK,
    IssueKind.INGREDIENT_IDLE: c.PERMISSION_INGREDIENTS,
    IssueKind.INGREDIENT_NO_MINIMUM: c.PERMISSION_INGREDIENTS,
    IssueKind.INGREDIENT_UNUSED: c.PERMISSION_INGREDIENTS,
    IssueKind.MARGIN_BELOW_TARGET: c.PERMISSION_RECIPE_COST,
    IssueKind.MENU_WITHOUT_RECIPE: c.PERMISSION_RECIPES,
    IssueKind.MENU_SHOULD_BE_VARIANT: c.PERMISSION_MENU,
    IssueKind.MENU_UNSOLD: c.PERMISSION_MENU,
    IssueKind.PROMO_ENDING: c.PERMISSION_PROMO,
    IssueKind.PROMO_UNUSED: c.PERMISSION_PROMO,
    IssueKind.LEAVE_WAITING: c.PERMISSION_ATTENDANCE,
    IssueKind.USER_UNSCHEDULED: c.PERMISSION_SCHEDULE,
    IssueKind.BRANCH_WITHOUT_USERS: c.PERMISSION_SCHEDULE,
    IssueKind.NO_CLOCK_IN: c.PERMISSION_ATTENDANCE,
    IssueKind.NO_CLOCK_OUT: c.PERMISSION_ATTENDANCE,
    IssueKind.AUTO_CLOSED: c.PERMISSION_ATTENDANCE,
    IssueKind.LATE_REPEATED: c.PERMISSION_ATTENDANCE,
    IssueKind.OVERTIME_OPEN: c.PERMISSION_ATTENDANCE,
    IssueKind.USER_UNPLACED: c.PERMISSION_USER,
    IssueKind.TASK_MISSED: c.PERMISSION_TASKS,
    IssueKind.DEVICE_IDLE: c.PERMISSION_DEVICES,
    IssueKind.DEVICE_CODE_EXPIRED: c.PERMISSION_DEVICES,
}

DETECTORS: tuple[Detector, ...] = (
    Detector(money.expense_over_income, (IssueKind.EXPENSE_OVER_INCOME,)),
    Detector(
        money.closed_sessions,
        (IssueKind.CASH_DIFFERENCE, IssueKind.DRAWER_OVER_CASH, IssueKind.FLOAT_DIFFERENCE, IssueKind.SHOPPING_DIFFERENCE),
    ),
    Detector(money.sessions_left_open, (IssueKind.SESSION_LEFT_OPEN,)),
    Detector(money.deposits_held, (IssueKind.DEPOSIT_HELD,)),
    Detector(money.non_cash_checks, (IssueKind.NON_CASH_UNCHECKED, IssueKind.NON_CASH_MISMATCH)),
    Detector(money.overpayments, (IssueKind.OVERPAYMENT,)),
    Detector(money.voids_many, (IssueKind.VOIDS_MANY,)),
    Detector(money.cancellations_waiting, (IssueKind.CANCELLATION_WAITING,)),
    Detector(stations.orders_off_board, (IssueKind.ORDER_OFF_BOARD,)),
    Detector(stock.stock_levels, (IssueKind.STOCK_OUT, IssueKind.STOCK_NEGATIVE, IssueKind.STOCK_LOW)),
    Detector(stock.counts_over_tolerance, (IssueKind.COUNT_OVER_TOLERANCE,)),
    Detector(stock.count_requests_waiting, (IssueKind.COUNT_REQUEST_WAITING,)),
    Detector(stock.openings_missing, (IssueKind.OPENING_MISSING,)),
    Detector(stock.purchase_price_jumps, (IssueKind.PURCHASE_PRICE_JUMP,)),
    Detector(stock.idle_ingredients, (IssueKind.INGREDIENT_IDLE,)),
    Detector(stock.without_minimum, (IssueKind.INGREDIENT_NO_MINIMUM,)),
    Detector(stock.unused_ingredients, (IssueKind.INGREDIENT_UNUSED,)),
    Detector(menu.recipes_and_margins, (IssueKind.MARGIN_BELOW_TARGET, IssueKind.MENU_WITHOUT_RECIPE)),
    Detector(menu.menus_for_one_variant, (IssueKind.MENU_SHOULD_BE_VARIANT,)),
    Detector(menu.unsold_menus, (IssueKind.MENU_UNSOLD,)),
    Detector(menu.promotions_ending, (IssueKind.PROMO_ENDING,)),
    Detector(menu.unused_promos, (IssueKind.PROMO_UNUSED,)),
    Detector(people.leave_waiting, (IssueKind.LEAVE_WAITING,)),
    Detector(people.schedule_ahead, (IssueKind.USER_UNSCHEDULED, IssueKind.BRANCH_WITHOUT_USERS)),
    Detector(people.no_clock_in, (IssueKind.NO_CLOCK_IN,)),
    Detector(people.attendance_left_open, (IssueKind.NO_CLOCK_OUT, IssueKind.AUTO_CLOSED)),
    Detector(people.late_repeated, (IssueKind.LATE_REPEATED,)),
    Detector(people.overtime_left_open, (IssueKind.OVERTIME_OPEN,)),
    Detector(people.user_unplaced, (IssueKind.USER_UNPLACED,)),
    Detector(branch.tasks_missed, (IssueKind.TASK_MISSED,)),
    Detector(branch.quiet_devices, (IssueKind.DEVICE_IDLE, IssueKind.DEVICE_CODE_EXPIRED)),
)
