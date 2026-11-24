"""Tab Stasiun & Printer di halaman detail cabang: siapa memegang dan mencetak tiap stasiun, dan pratinjau rute satu menu."""
from sqlalchemy.orm import Session

from app.core.devices import print_routing
from app.core.errors import DomainError
from app.models.outlet import Outlet
from app.models.user import User
from web.management.printers.schemas import MenuRouteOut, RouteDeviceOut, RoutePrinterOut, StationRouteOut, StationRoutesOut

NOT_FOUND = 404
OUTLET_NOT_FOUND = "Cabang tidak ditemukan. Muat ulang halaman, lalu pilih cabang lagi."


def route_out(route: print_routing.StationRoute) -> StationRouteOut:
    return StationRouteOut(
        station_id=route.station.id,
        station_name=route.station.name,
        kind=route.station.kind,
        holders=[RouteDeviceOut(device_id=holder.device_id, name=holder.name) for holder in route.holders],
        sender=RouteDeviceOut(device_id=route.sender.device_id, name=route.sender.name) if route.sender else None,
        printer=RoutePrinterOut(name=route.printer.name, connected=route.printer.connected) if route.printer else None,
        state=route.state,
        category_names=route.category_names,
    )


def stations(db: Session, user: User, outlet_id: str) -> StationRoutesOut:
    outlet = _outlet(db, user, outlet_id)
    return StationRoutesOut(outlet_id=outlet.id, stations=[route_out(route) for route in print_routing.routes(db, outlet.id)])


def menu_route(db: Session, user: User, outlet_id: str, menu_id: str) -> MenuRouteOut:
    outlet = _outlet(db, user, outlet_id)
    found = print_routing.route_of_menu(db, outlet.id, menu_id)
    return MenuRouteOut(menu_name=found.menu_name, category_name=found.category_name, route=route_out(found.route) if found.route else None)


def _outlet(db: Session, user: User, outlet_id: str) -> Outlet:
    """Akun yang terikat cabang hanya melihat cabangnya sendiri, apa pun isi URL-nya."""
    outlet = db.get(Outlet, outlet_id)
    if outlet is None or (user.locked_outlet_id and user.locked_outlet_id != outlet.id):
        raise DomainError(OUTLET_NOT_FOUND, status=NOT_FOUND)
    return outlet
