from pydantic import BaseModel

from app.core.devices.print_routing import RouteState
from app.models.station import StationKind


class RouteDeviceOut(BaseModel):
    device_id: str
    name: str


class RoutePrinterOut(BaseModel):
    name: str
    connected: bool


class StationRouteOut(BaseModel):
    station_id: str
    station_name: str
    kind: StationKind
    # Tablet yang memegang stasiun ini; kosong berarti stasiun ini tanpa layar di cabang ini.
    holders: list[RouteDeviceOut]
    # Tablet yang mengirim struk ke printer stasiun ini; kosong bila tidak mencetak.
    sender: RouteDeviceOut | None
    printer: RoutePrinterOut | None
    state: RouteState
    category_names: list[str]


class StationRoutesOut(BaseModel):
    outlet_id: str
    stations: list[StationRouteOut]


class MenuRouteOut(BaseModel):
    menu_name: str
    category_name: str | None
    route: StationRouteOut | None
