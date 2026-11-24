"""Every route of the management web (administration and reports); server.py mounts it here.

Sign-in is shared with the app (/v2/auth). Nothing under app/ may import this package.
"""
from fastapi import APIRouter, Depends

from web.management.access import web_user
from web.management.attendance import routes as attendance
from web.management.attendance_rules import routes as attendance_rules
from web.management.cafe_settings import routes as cafe_settings
from web.management.devices import routes as devices
from web.management.ingredients import routes as ingredients
from web.management.ingredient_movements import routes as ingredient_movements
from web.management.ingredient_count_requests import routes as ingredient_count_requests
from web.management.ingredient_counts import routes as ingredient_counts
from web.management.issues import routes as issues
from web.management.stock_items import routes as stock_items
from web.management.batches import routes as batches
from web.management.branches import routes as branches
from web.management.deposits import routes as deposits
from web.management.expenses import routes as expenses
from web.management.exports import routes as exports
from web.management.leave_requests import routes as leave_requests
from web.management.live import routes as live
from web.management.menu import routes as menu
from web.management.menu import cost_routes as menu_cost
from web.management.menu_categories import routes as menu_categories
from web.management.mutations import routes as mutations
from web.management.non_cash_checks import routes as non_cash_checks
from web.management.cancellations import routes as cancellations
from web.management.stations import routes as stations
from web.management.options import routes as options
from web.management.money_changes import routes as money_changes
from web.management.order_notes import routes as order_notes
from web.management.printers import routes as printers
from web.management.promotions import routes as promotions
from web.management.outlets import routes as outlets
from web.management.payment_methods import routes as payment_methods
from web.management.recipes import routes as recipes
from web.management.reports.inventory.ingredient_stock import routes as ingredient_stock_report
from web.management.reports.inventory.inventory_value import routes as inventory_value_report
from web.management.reports.inventory.low_stock import routes as low_stock_report
from web.management.reports.inventory.stock_turnover import routes as stock_turnover_report
from web.management.reports.menu.busy_products import routes as busy_products_report
from web.management.reports.menu.busy_sales import routes as busy_sales_report
from web.management.reports.menu.categories import routes as categories_report
from web.management.reports.menu.extras import routes as extras_report
from web.management.reports.menu.kitchen import routes as kitchen_report
from web.management.reports.menu.variants import routes as variants_report
from web.management.reports.menu.voids import routes as voids_report
from web.management.reports.people.attendance_recap import routes as attendance_recap_report
from web.management.reports.sales.cashiers import routes as cashiers_report
from web.management.reports.sales.breakdown import routes as sales_breakdown_report
from web.management.reports.sales.comparison import routes as comparison_report
from web.management.reports.sales.customers import routes as customers_report
from web.management.reports.sales.daily_overview import routes as daily_overview_report
from web.management.reports.sales.profit_loss import routes as profit_loss_report
from web.management.reports.sales.summary import routes as summary_report
from web.management.reports.sales.trend import routes as trend_report
from web.management.reports.sales.visitor_breakdown import routes as visitor_breakdown_report
from web.management.reports.transactions.listing import routes as listing_report
from web.management.reports.transactions.margin import routes as margin_report
from web.management.reports.transactions.overpayments import routes as overpayments_report
from web.management.reports.transactions.promos import routes as promos_report
from web.management.releases import routes as releases
from web.management.roles import routes as roles
from web.management.screens import routes as screens
from web.management.schedule.assignments import routes as schedule_assignments
from web.management.schedule.days_off import routes as schedule_days_off
from web.management.schedule.user_pool import routes as schedule_user_pool
from web.management.session_history import routes as session_history
from web.management.sessions import routes as sessions
from web.management.shift_categories import routes as shift_categories
from web.management.shift_code_groups import routes as shift_code_groups
from web.management.shift_codes import routes as shift_codes
from web.management.sop import routes as sop
from web.management.users import routes as user
from web.management.user_performance import routes as user_performance

# A route added here must decide whether its read is cached or never cached, following the rules in doc/CACHE.excalidraw.
# A read that has not been decided stays uncached, and a write never reads from the cache.
# Every route below first checks that the account may use the management web at all (web/management/access.py).
router = APIRouter(prefix="/web/management", dependencies=[Depends(web_user)])
router.include_router(live.router)
router.include_router(exports.router)
router.include_router(issues.router)
router.include_router(screens.router)
router.include_router(releases.router)
router.include_router(deposits.router)
router.include_router(outlets.router)
router.include_router(branches.router)
router.include_router(sessions.router)
router.include_router(non_cash_checks.router)
router.include_router(cancellations.router)
router.include_router(stations.router)
router.include_router(payment_methods.router)
router.include_router(mutations.router)
router.include_router(session_history.router)
router.include_router(expenses.router)
router.include_router(menu.router)
router.include_router(menu_categories.router)
router.include_router(recipes.router)
router.include_router(options.router)
router.include_router(order_notes.router)
router.include_router(money_changes.router)
router.include_router(promotions.router)
router.include_router(roles.router)
router.include_router(user.router)
router.include_router(shift_codes.router)
router.include_router(shift_code_groups.router)
router.include_router(shift_categories.router)
router.include_router(batches.router)
router.include_router(attendance.router)
router.include_router(attendance_rules.router)
router.include_router(cafe_settings.router)
router.include_router(devices.router)
router.include_router(ingredients.router)
router.include_router(ingredient_movements.router)
router.include_router(ingredient_counts.router)
router.include_router(printers.router)
router.include_router(stock_items.router)
router.include_router(leave_requests.router)
router.include_router(sop.router)
router.include_router(schedule_assignments.router)
router.include_router(schedule_days_off.router)
router.include_router(schedule_user_pool.router)
router.include_router(summary_report.router)
router.include_router(trend_report.router)
router.include_router(comparison_report.router)
router.include_router(cashiers_report.router)
router.include_router(daily_overview_report.router)
router.include_router(profit_loss_report.router)
router.include_router(listing_report.router)
router.include_router(overpayments_report.router)
router.include_router(margin_report.router)
router.include_router(promos_report.router)
router.include_router(busy_sales_report.router)
router.include_router(busy_products_report.router)
router.include_router(categories_report.router)
router.include_router(kitchen_report.router)
router.include_router(voids_report.router)
router.include_router(variants_report.router)
router.include_router(extras_report.router)
router.include_router(ingredient_stock_report.router)
router.include_router(stock_turnover_report.router)
router.include_router(inventory_value_report.router)
router.include_router(low_stock_report.router)
router.include_router(visitor_breakdown_report.router)
router.include_router(attendance_recap_report.router)
router.include_router(user_performance.router)
router.include_router(menu_cost.router)
router.include_router(ingredient_count_requests.router)
router.include_router(customers_report.router)
router.include_router(sales_breakdown_report.router)
