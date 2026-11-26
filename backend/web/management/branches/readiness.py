"""Kesiapan cabang: yang masih kurang sebelum kasir bisa bertransaksi, dibaca dari aturan yang sama dengan penolakan di kasir."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.catalog import branch_scope
from app.core.devices import print_routing
from app.core.finance import payment_methods, session_control
from app.core.orders import create as order_rules
from app.core.orders import lines as line_rules
from app.models.cafe_settings import CafeSettings
from app.models.menu_item import MenuItem
from app.models.station import StationKind
from app.models.user import User
from web.management.branches import service
from web.management.branches.schemas import BranchReadinessOut
from web.management.printers.service import route_out

# Cukup untuk menunjuk menu mana yang perlu dibenahi; jumlah lengkapnya tetap dikirim terpisah.
NAMED_MENU_LIMIT = 5
CASHIER_PERMISSIONS = (order_rules.PERMISSION, session_control.PERMISSION_OPEN)


def _unpriced_menus(db: Session, outlet_id: str) -> tuple[int, list[str], int]:
    """(menu yang dijual cabang ini, nama menu tanpa resep atau harga pokok, jumlahnya), dengan jumlah query tetap."""
    menus = db.execute(
        select(MenuItem.id, MenuItem.name)
        .where(branch_scope.listed_at_clause(MenuItem.outlet_ids, outlet_id), MenuItem.is_available.is_(True))
        .order_by(MenuItem.name, MenuItem.id)
    ).all()
    ready = line_rules.ready_ids(db, outlet_id, [menu_id for menu_id, _ in menus])
    unpriced = [name for menu_id, name in menus if menu_id not in ready]
    return len(menus), unpriced[:NAMED_MENU_LIMIT], len(unpriced)


def _cashier_staff_count(db: Session, outlet_id: str) -> int:
    """Akun aktif yang ditempatkan di cabang ini dan boleh membuka sesi kas serta mencatat transaksi."""
    staff = db.scalars(select(User).where(User.outlet_id == outlet_id, User.is_active.is_(True), User.deleted_at.is_(None))).all()
    return sum(1 for user in staff if all(user.allows(permission) for permission in CASHIER_PERMISSIONS))


def readiness(db: Session, admin: User, outlet_id: str) -> BranchReadinessOut:
    outlet = service.get(db, admin, outlet_id)
    routes = print_routing.routes(db, outlet.id)
    cashier = next((route.holders[0].name for route in routes if route.station.kind == StationKind.HANDOVER and route.holders), None)
    menu_count, unpriced_names, unpriced_count = _unpriced_menus(db, outlet.id)
    methods = payment_methods.methods_of(db, outlet.id)
    return BranchReadinessOut(
        settings_ready=db.get(CafeSettings, outlet.id) is not None,
        location_ready=outlet.latitude is not None and outlet.longitude is not None,
        cashier_name=cashier,
        stations=[route_out(route) for route in routes],
        menu_count=menu_count,
        unpriced_menu_count=unpriced_count,
        unpriced_menu_names=unpriced_names,
        open_payment_labels=[method.label for method in methods if payment_methods.is_open(method)],
        incomplete_payment_labels=[method.label for method in methods if method.is_active and payment_methods.missing_requirements(method)],
        cashier_staff_count=_cashier_staff_count(db, outlet.id),
    )
