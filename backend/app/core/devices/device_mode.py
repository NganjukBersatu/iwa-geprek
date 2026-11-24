"""Satu pintu mode tablet: Mode Kasir memegang Kasir dan mencetak stasiun lain yang dicentang saat pesanan dibuat; Mode Stasiun memegang semua yang dicentang."""
from sqlalchemy import select, union_all
from sqlalchemy.orm import Session

from app.core.devices import device_stations, print_routing
from app.core.errors import DomainError
from app.models.device import MODE_CASHIER, MODES, Device
from app.models.station import DeviceStation, DeviceStationPrint, Station, StationKind

NOT_FOUND = 404
MODE_UNKNOWN = "Pilih Mode Kasir atau Mode Stasiun."
NEEDS_CASHIER = "Mode Kasir butuh stasiun Kasir. Centang Kasir, atau pilih Mode Stasiun."
TAKEN = "Stasiun {station} sudah dipakai {device} di cabang ini. Lepaskan dulu dari tablet itu."


def configure(db: Session, device: Device, mode: str, station_ids: list[str]) -> None:
    """Menetapkan mode dan stasiun yang dicentang; pemanggil yang menyelaraskan stasiun aktif cabang dan menyimpan."""
    if mode not in MODES:
        raise DomainError(MODE_UNKNOWN)
    device_stations.require_stations(station_ids)
    wanted = sorted(set(station_ids))
    stations = {station.id: station for station in db.scalars(select(Station).where(Station.id.in_(wanted))).all()}
    if len(stations) != len(wanted):
        raise DomainError(device_stations.STATION_NOT_FOUND, status=NOT_FOUND)
    _require_free(db, device, [station for station in stations.values() if station.kind != StationKind.HANDOVER])
    if mode == MODE_CASHIER:
        held = [station_id for station_id in wanted if stations[station_id].kind == StationKind.HANDOVER]
        if not held:
            raise DomainError(NEEDS_CASHIER)
        printed = [station_id for station_id in wanted if station_id not in held]
    else:
        held, printed = wanted, []
    device_stations.set_stations(db, device, held)
    print_routing.set_prints(db, device, held, printed)
    device.mode = mode
    db.flush()


def station_users(db: Session, outlet_id: str) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Tablet cabang ini (apa pun statusnya) yang memegang tiap stasiun, dan yang mencetaknya dari kasir; dua query."""
    held: dict[str, list[str]] = {}
    for station_id, device_id in db.execute(
        select(DeviceStation.station_id, DeviceStation.device_id).join(Device, Device.id == DeviceStation.device_id).where(Device.outlet_id == outlet_id).order_by(Device.name, Device.id)
    ).all():
        held.setdefault(station_id, []).append(device_id)
    printed: dict[str, list[str]] = {}
    for station_id, device_id in db.execute(
        select(DeviceStationPrint.station_id, DeviceStationPrint.device_id).join(Device, Device.id == DeviceStationPrint.device_id).where(Device.outlet_id == outlet_id).order_by(Device.name, Device.id)
    ).all():
        printed.setdefault(station_id, []).append(device_id)
    return held, printed


def _require_free(db: Session, device: Device, stations: list[Station]) -> None:
    """Stasiun selain Kasir hanya milik satu tablet di satu cabang, dipegang maupun dicetak dari kasir."""
    if not stations:
        return
    ids = [station.id for station in stations]
    used = union_all(
        select(DeviceStation.station_id, DeviceStation.device_id).where(DeviceStation.station_id.in_(ids)),
        select(DeviceStationPrint.station_id, DeviceStationPrint.device_id).where(DeviceStationPrint.station_id.in_(ids)),
    ).subquery()
    taken = db.execute(
        select(used.c.station_id, Device.name)
        .join(Device, Device.id == used.c.device_id)
        .where(Device.outlet_id == device.outlet_id, Device.id != device.id)
        .order_by(used.c.station_id, Device.name)
        .limit(1)
    ).first()
    if taken is not None:
        name = next(station.name for station in stations if station.id == taken.station_id)
        raise DomainError(TAKEN.format(station=name, device=taken.name))
