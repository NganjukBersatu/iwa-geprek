"""HTTP surface of the devices; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import readable_outlet_id, require_permission, writable_outlet_id
from app.core.branches import outlet_names
from app.core.database import get_db
from app.core.devices import device_mode, device_stations, print_routing
from app.core.errors import DomainError
from app.core.sorting import RowSorting, Sort
from app.core.user_names import user_names
from app.models.device import Device
from app.models.station import Station
from app.models.user import User
from web.management.devices import service
from web.management.devices.constants import PERMISSION_MANAGE
from web.management.devices.schemas import DeviceCodeOut, DeviceCreateIn, DeviceOut, DeviceUpdateIn, StationOptionOut

router = APIRouter(prefix="/devices", tags=["v2-devices"])

NO_STORE = "no-store"


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


SORTING: RowSorting[DeviceOut] = RowSorting(
    keys={
        "name": lambda row: row.name,
        "outlet": lambda row: row.outlet_name,
        "last_used": lambda row: row.last_used_at,
        "status": lambda row: row.status,
    },
    identity=lambda row: row.id,
)


COMPUTED = {"outlet_name", "station_ids", "station_names", "print_station_ids", "print_station_names", "registered_by_name"}


@dataclass(frozen=True)
class _Lookups:
    outlets: dict[str, str]
    held: dict[str, list[str]]
    prints: dict[str, list[str]]
    stations: dict[str, str]
    admins: dict[str, str]


def _out(device: Device, lookups: _Lookups) -> DeviceOut:
    fields = {name: getattr(device, name) for name in DeviceOut.model_fields if name not in COMPUTED}
    held = lookups.held.get(device.id, [])
    printed = lookups.prints.get(device.id, [])
    return DeviceOut(
        outlet_name=lookups.outlets.get(device.outlet_id, ""),
        station_ids=held,
        station_names=[lookups.stations.get(station_id, "") for station_id in held],
        print_station_ids=printed,
        print_station_names=[lookups.stations.get(station_id, "") for station_id in printed],
        registered_by_name=lookups.admins.get(device.registered_by) if device.registered_by else None,
        **fields,
    )


def _names(db: Session, devices: list[Device]) -> _Lookups:
    ids = [device.id for device in devices]
    held = device_stations.held_ids(db, ids)
    prints = print_routing.prints_of(db, ids)
    wanted = {station_id for group in (held, prints) for station_ids in group.values() for station_id in station_ids}
    stations = dict(db.execute(select(Station.id, Station.name).where(Station.id.in_(wanted))).all()) if wanted else {}
    admins = user_names(db, [device.registered_by for device in devices])
    return _Lookups(outlet_names(db, [device.outlet_id for device in devices]), held, prints, stations, admins)


def _with_code(db: Session, device: Device, code: str) -> DeviceCodeOut:
    return DeviceCodeOut(**_out(device, _names(db, [device])).model_dump(), code=code, code_expires_at=device.code_expires_at)


@router.get("", response_model=list[DeviceOut])
def list_devices(
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    devices = service.list_devices(db, outlet_id)
    names = _names(db, devices)
    return SORTING.apply([_out(device, names) for device in devices], sort)


# Tidak di-cache: daftar kecil yang harus langsung benar setelah tablet dipasangkan atau stasiunnya diubah.
@router.get("/stations", response_model=list[StationOptionOut])
def station_options(
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    if outlet_id is None:
        return []
    held, printed = device_mode.station_users(db, outlet_id)
    return [
        StationOptionOut(id=station.id, name=station.name, kind=station.kind, device_names=names, holder_device_ids=held.get(station.id, []), printer_device_ids=printed.get(station.id, []))
        for station, names in device_stations.options(db, outlet_id)
    ]


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(
    device_id: str,
    response: Response,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    response.headers["Cache-Control"] = NO_STORE
    with _domain_errors():
        device = service.get(db, outlet_id, device_id)
    return _out(device, _names(db, [device]))


@router.post("", response_model=DeviceCodeOut, status_code=status.HTTP_201_CREATED)
def create_device(
    body: DeviceCreateIn,
    response: Response,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    admin: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    response.headers["Cache-Control"] = NO_STORE
    with _domain_errors():
        device, code = service.create(db, admin, outlet_id, body.name, body.station_ids, body.print_station_ids, body.mode)
    return _with_code(db, device, code)


@router.patch("/{device_id}", response_model=DeviceOut)
def update_device(
    device_id: str,
    body: DeviceUpdateIn,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        device = service.update(db, outlet_id, device_id, body.model_dump(exclude_unset=True))
    return _out(device, _names(db, [device]))


@router.post("/{device_id}/new-code", response_model=DeviceCodeOut)
def new_code(
    device_id: str,
    response: Response,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    response.headers["Cache-Control"] = NO_STORE
    with _domain_errors():
        device, code = service.new_code(db, outlet_id, device_id)
    return _with_code(db, device, code)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_device(
    device_id: str,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.revoke(db, outlet_id, device_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
