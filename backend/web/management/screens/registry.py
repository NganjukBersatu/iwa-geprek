from enum import StrEnum

from app.core.auth import EVERY_USER, FULL_ACCESS_ONLY, AnyOf, EveryUser, Gate, passes
from app.core.catalog import options, recipe_book
from app.core.orders.cancellations import PERMISSION_DECIDE as CANCELLATIONS_DECIDE
from app.core.orders.notes import PERMISSION_MANAGE as ORDER_NOTES_MANAGE
from app.core.orders.station_setup import PERMISSION_MANAGE as STATIONS_MANAGE
from app.core.orders.stations import PERMISSION_INTERVENE as STATIONS_INTERVENE
from app.employee.schedule.constants import PERMISSION_MANAGE as SCHEDULE_MANAGE
from app.employee.schedule.constants import PERMISSION_VIEW as SCHEDULE_VIEW
from app.employee.tasks.constants import PERMISSION_VIEW as TASKS_VIEW
from app.models.user import User
from app.core.finance import expenses as expense_rules
from app.core.finance import sessions as session_rules
from web.management.attendance.constants import PERMISSION_MANAGE as ATTENDANCE_MANAGE
from web.management.attendance_rules.constants import PERMISSION_MANAGE as ATTENDANCE_RULES_MANAGE
from web.management.branches.constants import PERMISSION_MANAGE as BRANCHES_MANAGE
from web.management.branches.constants import PERMISSION_REMOVE as BRANCHES_REMOVE
from web.management.branches.constants import READ_GATE as BRANCHES_READ
from web.management.branches.constants import READINESS_GATE as BRANCHES_READINESS
from web.management.cafe_settings.constants import PERMISSION_MANAGE as CAFE_SETTINGS_MANAGE
from web.management.deposits.constants import PERMISSION_MANAGE as DEPOSITS_MANAGE, PERMISSION_VIEW as DEPOSITS_VIEW
from web.management.devices.constants import PERMISSION_MANAGE as DEVICES_MANAGE
from web.management.batches.constants import PERMISSION_MANAGE as TASKS_MANAGE
from web.management.ingredient_counts.constants import PERMISSION_COUNT as STOCK_COUNT
from web.management.ingredient_counts.constants import PERMISSION_REQUEST as STOCK_REQUEST
from web.management.ingredient_counts.constants import PERMISSION_VIEW as COUNTS_VIEW
from web.management.ingredient_movements.constants import PERMISSION_ADJUST as STOCK_ADJUST
from web.management.ingredient_movements.constants import PERMISSION_CORRECT as STOCK_CORRECT
from web.management.ingredient_movements.constants import PERMISSION_RECEIVE as STOCK_RECEIVE
from web.management.ingredient_movements.constants import PERMISSION_VIEW as MOVEMENTS_VIEW
from web.management.ingredients.constants import PERMISSION_MANAGE as INGREDIENTS_MANAGE
from web.management.ingredients.constants import PERMISSION_VIEW as INGREDIENTS_VIEW
from web.management.issues.registry import PERMISSION_OF as ISSUE_GATES
from web.management.menu.routes import PERMISSION_MANAGE as MENU_MANAGE
from web.management.mutations.routes import PERMISSION_VIEW as MUTATIONS_VIEW
from web.management.payment_methods.constants import PERMISSION_MANAGE as PAYMENT_METHODS_MANAGE
from web.management.promotions.routes import PERMISSION_MANAGE as PROMOTIONS_MANAGE
from web.management.reports import gates as report_gates
from web.management.reports.people.attendance_recap.constants import RECAP_GATE
from web.management.roles.constants import PERMISSION_MANAGE as ROLES_MANAGE
from web.management.session_history.routes import PERMISSION_VIEW_ALL as SESSIONS_VIEW_ALL
from web.management.session_history.routes import PERMISSION_VOID as ORDERS_VOID
from web.management.shift_codes.constants import PERMISSION_MANAGE as SHIFT_CODES_MANAGE
from web.management.sop.constants import PERMISSION_MANAGE as SOP_MANAGE
from web.management.users.constants import PERMISSION_MANAGE as USER_MANAGE
from web.management.stations.routes import MONITOR_GATE as STATIONS_MONITOR
from web.management.stock_items.constants import PERMISSION_MANAGE as STOCK_ITEMS_MANAGE
from web.management.stock_items.constants import PERMISSION_VIEW as STOCK_ITEMS_VIEW


class Screen(StrEnum):
    DASHBOARD = "dashboard"
    ISSUES = "issues"
    FINANCE_OVERVIEW = "finance_overview"
    BUSY_SALES = "busy_sales"
    BUSY_PRODUCTS = "busy_products"
    CATEGORIES_REPORT = "categories_report"
    OPTIONS_REPORT = "options_report"
    PROMOS_REPORT = "promos_report"
    VOIDS_REPORT = "voids_report"
    VISITORS_REPORT = "visitors_report"
    INGREDIENT_STOCK_REPORT = "ingredient_stock_report"
    STOCK_TURNOVER_REPORT = "stock_turnover_report"
    ATTENDANCE_REPORT = "attendance_report"
    MARGIN = "margin"
    MENU = "menu"
    MENU_CATEGORIES = "menu_categories"
    OPTIONS = "options"
    RECIPES = "recipes"
    PROMOTIONS = "promotions"
    ORDER_NOTES = "order_notes"
    MONEY_CHANGES = "money_changes"
    STATION_MONITOR = "station_monitor"
    STATION_PERFORMANCE = "station_performance"
    STATION_TARGETS = "station_targets"
    STATION_SETUP = "station_setup"
    INGREDIENTS = "ingredients"
    INDIRECT_INGREDIENTS = "indirect_ingredients"
    INGREDIENT_RECEIPTS = "ingredient_receipts"
    INGREDIENT_WASTE = "ingredient_waste"
    INGREDIENT_COUNTS = "ingredient_counts"
    STOCK_ITEMS = "stock_items"
    SESSION_HISTORY = "session_history"
    OVERPAYMENTS = "overpayments"
    EXPENSES = "expenses"
    MUTATIONS = "mutations"
    PAYMENT_METHODS = "payment_methods"
    USERS = "users"
    ROLES = "roles"
    SCHEDULE = "schedule"
    SHIFT_CODES = "shift_codes"
    ATTENDANCE = "attendance"
    SOP = "sop"
    TASKS = "tasks"
    BRANCHES = "branches"
    CAFE_SETTINGS = "cafe_settings"
    DEVICES = "devices"
    PRINTERS = "printers"
    ATTENDANCE_RULES = "attendance_rules"


def _issues_gate() -> Gate:
    """The page opens for whoever may see at least one kind of issue; a kind open to everyone opens it for everyone."""
    keys: set[str] = set()
    for gate in ISSUE_GATES.values():
        if isinstance(gate, EveryUser):
            return EVERY_USER
        if isinstance(gate, str):
            keys.add(gate)
        elif isinstance(gate, AnyOf):
            keys.update(gate.keys)
    return AnyOf(tuple(sorted(keys)))


# Each gate is the one guarding the read the screen opens with; sections inside a screen keep their own checks.
GATE_OF: dict[Screen, Gate] = {
    Screen.DASHBOARD: report_gates.DASHBOARD,
    # Every kind of issue is already limited to whoever may see its data.
    Screen.ISSUES: _issues_gate(),
    Screen.FINANCE_OVERVIEW: report_gates.OVERVIEW,
    Screen.BUSY_SALES: report_gates.BUSY_SALES,
    Screen.BUSY_PRODUCTS: report_gates.BUSY_PRODUCTS,
    Screen.CATEGORIES_REPORT: report_gates.CATEGORIES,
    Screen.OPTIONS_REPORT: report_gates.OPTIONS,
    Screen.PROMOS_REPORT: report_gates.PROMOS,
    Screen.VOIDS_REPORT: report_gates.VOIDS,
    Screen.VISITORS_REPORT: report_gates.VISITORS,
    Screen.INGREDIENT_STOCK_REPORT: report_gates.INGREDIENT_STOCK,
    Screen.STOCK_TURNOVER_REPORT: report_gates.STOCK_TURNOVER,
    Screen.ATTENDANCE_REPORT: RECAP_GATE,
    Screen.MARGIN: report_gates.MARGIN,
    Screen.MENU: MENU_MANAGE,
    Screen.MENU_CATEGORIES: MENU_MANAGE,
    Screen.OPTIONS: options.MANAGE_GATE,
    Screen.RECIPES: recipe_book.READ_GATE,
    Screen.PROMOTIONS: PROMOTIONS_MANAGE,
    Screen.ORDER_NOTES: ORDER_NOTES_MANAGE,
    Screen.MONEY_CHANGES: SESSIONS_VIEW_ALL,
    Screen.STATION_MONITOR: STATIONS_MONITOR,
    Screen.STATION_PERFORMANCE: report_gates.STATION_PERFORMANCE,
    Screen.STATION_TARGETS: STATIONS_MANAGE,
    Screen.STATION_SETUP: STATIONS_MANAGE,
    Screen.INGREDIENTS: INGREDIENTS_VIEW,
    Screen.INDIRECT_INGREDIENTS: INGREDIENTS_VIEW,
    Screen.INGREDIENT_RECEIPTS: MOVEMENTS_VIEW,
    Screen.INGREDIENT_WASTE: MOVEMENTS_VIEW,
    Screen.INGREDIENT_COUNTS: COUNTS_VIEW,
    Screen.STOCK_ITEMS: STOCK_ITEMS_VIEW,
    Screen.SESSION_HISTORY: SESSIONS_VIEW_ALL,
    Screen.OVERPAYMENTS: FULL_ACCESS_ONLY,
    # Without the see-all permission the list holds only the account's own expenses.
    Screen.EXPENSES: AnyOf((expense_rules.PERMISSION_RECORD, expense_rules.PERMISSION_VIEW_ALL, expense_rules.PERMISSION_EDIT_OWN, expense_rules.PERMISSION_EDIT_ALL)),
    Screen.MUTATIONS: MUTATIONS_VIEW,
    Screen.PAYMENT_METHODS: PAYMENT_METHODS_MANAGE,
    Screen.USERS: USER_MANAGE,
    Screen.ROLES: ROLES_MANAGE,
    Screen.SCHEDULE: SCHEDULE_VIEW,
    Screen.SHIFT_CODES: SHIFT_CODES_MANAGE,
    Screen.ATTENDANCE: ATTENDANCE_MANAGE,
    Screen.SOP: SOP_MANAGE,
    Screen.TASKS: TASKS_VIEW,
    Screen.BRANCHES: BRANCHES_READ,
    Screen.CAFE_SETTINGS: CAFE_SETTINGS_MANAGE,
    Screen.DEVICES: DEVICES_MANAGE,
    Screen.PRINTERS: DEVICES_MANAGE,
    Screen.ATTENDANCE_RULES: ATTENDANCE_RULES_MANAGE,
}


class Ability(StrEnum):
    """A part inside a screen that only some accounts may see or use."""

    DECIDE_CANCELLATIONS = "decide_cancellations"
    VIEW_DEPOSITS = "view_deposits"
    MANAGE_DEPOSITS = "manage_deposits"
    MANAGE_VARIANTS = "manage_variants"
    MANAGE_EXTRAS = "manage_extras"
    MANAGE_RECIPES = "manage_recipes"
    SEE_RECIPE_COSTS = "see_recipe_costs"
    ARRANGE_SCHEDULE = "arrange_schedule"
    MARK_ATTENDANCE = "mark_attendance"
    INTERVENE_STATIONS = "intervene_stations"
    # The cards of the dashboard, each shown only to who may see the report behind it.
    VIEW_SUMMARY = "view_summary"
    VIEW_TREND = "view_trend"
    VIEW_PROFIT_LOSS = "view_profit_loss"
    VIEW_INVENTORY_VALUE = "view_inventory_value"
    VIEW_CASHIER_FIGURES = "view_cashier_figures"
    VIEW_CUSTOMER_FIGURES = "view_customer_figures"
    VIEW_COMPARISON = "view_comparison"
    VIEW_TRANSACTION_LIST = "view_transaction_list"
    VALIDATE_NON_CASH = "validate_non_cash"
    # Writing on screens that open with a reading permission.
    RECEIVE_STOCK = "receive_stock"
    ADJUST_STOCK = "adjust_stock"
    COUNT_STOCK = "count_stock"
    REQUEST_STOCK_CLOSE = "request_stock_close"
    MANAGE_STOCK_ITEMS = "manage_stock_items"
    CORRECT_STOCK = "correct_stock"
    MANAGE_INGREDIENTS = "manage_ingredients"
    RECORD_EXPENSES = "record_expenses"
    EDIT_OWN_EXPENSES = "edit_own_expenses"
    EDIT_ALL_EXPENSES = "edit_all_expenses"
    CORRECT_SESSIONS = "correct_sessions"
    DELETE_SESSIONS = "delete_sessions"
    MANAGE_OWN_SESSIONS = "manage_own_sessions"
    EDIT_ORDERS = "edit_orders"
    DELETE_ORDERS = "delete_orders"
    VOID_ORDERS = "void_orders"
    MANAGE_ROLES = "manage_roles"
    MANAGE_TASKS = "manage_tasks"
    MANAGE_BRANCHES = "manage_branches"
    REMOVE_BRANCHES = "remove_branches"
    VIEW_SETUP_GUIDE = "view_setup_guide"


# Each gate is the one guarding the routes behind that part, so a part shown is a part the server will serve.
ABILITY_GATE: dict[Ability, Gate] = {
    Ability.DECIDE_CANCELLATIONS: CANCELLATIONS_DECIDE,
    Ability.VIEW_DEPOSITS: DEPOSITS_VIEW,
    Ability.MANAGE_DEPOSITS: DEPOSITS_MANAGE,
    Ability.MANAGE_VARIANTS: options.PERMISSION_VARIANTS,
    Ability.MANAGE_EXTRAS: options.PERMISSION_EXTRAS,
    Ability.MANAGE_RECIPES: recipe_book.PERMISSION_MANAGE,
    Ability.SEE_RECIPE_COSTS: recipe_book.PERMISSION_COST,
    Ability.ARRANGE_SCHEDULE: SCHEDULE_MANAGE,
    Ability.MARK_ATTENDANCE: ATTENDANCE_MANAGE,
    Ability.INTERVENE_STATIONS: STATIONS_INTERVENE,
    Ability.VIEW_SUMMARY: report_gates.SUMMARY,
    Ability.VIEW_TREND: report_gates.TREND,
    Ability.VIEW_PROFIT_LOSS: report_gates.PROFIT_LOSS,
    Ability.VIEW_INVENTORY_VALUE: report_gates.INVENTORY_VALUE,
    Ability.VIEW_CASHIER_FIGURES: report_gates.CASHIERS,
    Ability.VIEW_CUSTOMER_FIGURES: report_gates.CUSTOMERS,
    Ability.VIEW_COMPARISON: report_gates.COMPARISON,
    Ability.VIEW_TRANSACTION_LIST: report_gates.TRANSACTIONS,
    Ability.VALIDATE_NON_CASH: report_gates.VALIDATE_NON_CASH,
    Ability.RECEIVE_STOCK: STOCK_RECEIVE,
    Ability.ADJUST_STOCK: STOCK_ADJUST,
    Ability.COUNT_STOCK: STOCK_COUNT,
    Ability.REQUEST_STOCK_CLOSE: STOCK_REQUEST,
    Ability.MANAGE_STOCK_ITEMS: STOCK_ITEMS_MANAGE,
    Ability.CORRECT_STOCK: STOCK_CORRECT,
    Ability.MANAGE_INGREDIENTS: INGREDIENTS_MANAGE,
    Ability.RECORD_EXPENSES: expense_rules.PERMISSION_RECORD,
    Ability.EDIT_OWN_EXPENSES: expense_rules.PERMISSION_EDIT_OWN,
    Ability.EDIT_ALL_EXPENSES: expense_rules.PERMISSION_EDIT_ALL,
    Ability.CORRECT_SESSIONS: session_rules.PERMISSION_CORRECT,
    Ability.DELETE_SESSIONS: session_rules.PERMISSION_DELETE,
    Ability.MANAGE_OWN_SESSIONS: session_rules.PERMISSION_OWN,
    Ability.EDIT_ORDERS: session_rules.PERMISSION_EDIT_ORDER,
    Ability.DELETE_ORDERS: session_rules.PERMISSION_DELETE_ORDER,
    Ability.VOID_ORDERS: ORDERS_VOID,
    Ability.MANAGE_ROLES: ROLES_MANAGE,
    Ability.MANAGE_TASKS: TASKS_MANAGE,
    Ability.MANAGE_BRANCHES: BRANCHES_MANAGE,
    Ability.REMOVE_BRANCHES: BRANCHES_REMOVE,
    Ability.VIEW_SETUP_GUIDE: BRANCHES_READINESS,
}


def screens_of(user: User) -> list[Screen]:
    return [screen for screen, gate in GATE_OF.items() if passes(user, gate)]


def abilities_of(user: User) -> list[Ability]:
    return [ability for ability, gate in ABILITY_GATE.items() if passes(user, gate)]
