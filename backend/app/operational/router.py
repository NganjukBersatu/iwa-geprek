"""Every route of the operational tablet; app/router.py mounts it under /v2/operational."""
from fastapi import APIRouter

from app.operational.cancellations import routes as cancellations
from app.operational.cashier import routes as cashier
from app.operational.customers import routes as customers
from app.operational.expenses import routes as expenses
from app.operational.menu import routes as menu
from app.operational.options import routes as options
from app.operational.order_notes import routes as order_notes
from app.operational.orders import routes as orders
from app.operational.overpayments import routes as overpayments
from app.operational.printers import routes as printers
from app.operational.promotions import routes as promotions
from app.operational.recipes import routes as recipes
from app.operational.resale_stock import routes as resale_stock
from app.operational.periods import routes as periods
from app.operational.releases import routes as releases
from app.operational.sessions import routes as sessions
from app.operational.user_choices import routes as user_choices
from app.operational.stations import routes as stations
from app.operational.stock import routes as stock
from app.operational.visitors import routes as visitors

# A route added here must decide whether its read is cached or never cached, following the rules in doc/CACHE.excalidraw.
# A read that has not been decided stays uncached, and a write never reads from the cache.
router = APIRouter(prefix="/operational")
router.include_router(menu.router)
router.include_router(expenses.router)
router.include_router(cashier.router)
router.include_router(orders.router)
router.include_router(sessions.router)
router.include_router(overpayments.router)
router.include_router(options.router)
router.include_router(recipes.router)
router.include_router(promotions.router)
router.include_router(visitors.router)
router.include_router(stations.router)
router.include_router(releases.router)
router.include_router(cancellations.router)
router.include_router(order_notes.router)
router.include_router(stock.router)
router.include_router(resale_stock.router)
router.include_router(printers.router)
router.include_router(user_choices.router)
router.include_router(periods.router)
router.include_router(customers.router)
