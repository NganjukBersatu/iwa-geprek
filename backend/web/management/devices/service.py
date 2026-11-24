"""Registering the tablets of a branch: the admin creates one and hands over a one-time code."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import now
from app.core.devices import codes, device_mode, device_stations, print_routing
from app.core.errors import DomainError
from app.core.security import hash_token
from app.models.device import Device
from app.models.user import User
from web.management.devices import messages
from web.management.devices.constants import CODE_VALID_FOR, DEFAULT_SECTION, NOT_FOUND, WAITING_STATUS


def list_devices(db: Session, outlet_id: str | None) -> list[Device]:
    query = select(Device).order_by(Device.created_at)
    if outlet_id:
        query = query.where(Device.outlet_id == outlet_id)
    return list(db.scalars(query))


def get(db: Session, outlet_id: str | None, device_id: str) -> Device:
    """One device for its page; a device of another branch answers as missing for someone bound to one branch."""
    return _find(db, outlet_id, device_id)


def create(db: Session, admin: User, outlet_id: str, name: str, station_ids: list[str], print_station_ids: list[str], mode: str | None) -> tuple[Device, str]:
    tidy = name.strip()
    if not tidy:
        raise DomainError(messages.NAME_REQUIRED)
    device_stations.require_stations(station_ids)
    device = Device(outlet_id=outlet_id, name=tidy, section=DEFAULT_SECTION, status=WAITING_STATUS, registered_by=admin.id)
    db.add(device)
    db.flush()
    if mode is not None:
        device_mode.configure(db, device, mode, station_ids)
    else:
        device_stations.set_stations(db, device, station_ids)
        print_routing.set_prints(db, device, station_ids, print_station_ids)
    return device, _issue_code(db, device)


def update(db: Session, outlet_id: str | None, device_id: str, values: dict) -> Device:
    device = _find(db, outlet_id, device_id)
    tidy = values["name"].strip() if values.get("name") is not None else None
    if tidy == "":
        raise DomainError(messages.NAME_REQUIRED)
    mode = values.get("mode")
    if mode is not None:
        if tidy is not None:
            device.name = tidy
        checked = values.get("station_ids")
        if checked is None:
            # Mode diganti tanpa daftar stasiun: yang dicentang tetap sama, hanya cara cetaknya yang berubah.
            checked = device_stations.held_ids(db, [device.id]).get(device.id, []) + print_routing.prints_of(db, [device.id]).get(device.id, [])
        device_mode.configure(db, device, mode, checked)
        print_routing.sync_used(db, device.outlet_id)
        db.commit()
        return device
    wanted = values.get("station_ids")
    if wanted is not None:
        device_stations.require_stations(wanted)
    if tidy is not None:
        device.name = tidy
    if wanted is not None:
        device_stations.set_stations(db, device, wanted)
    printed = values.get("print_station_ids")
    if wanted is not None or printed is not None:
        held = wanted if wanted is not None else device_stations.held_ids(db, [device.id]).get(device.id, [])
        if printed is None:
            # Tablet yang dilepas dari Kasir otomatis berhenti mengirim struk stasiun tanpa tablet.
            printed = print_routing.prints_of(db, [device.id]).get(device.id, []) if print_routing.holds_cashier(db, held) else []
        print_routing.set_prints(db, device, held, printed)
    print_routing.sync_used(db, device.outlet_id)
    db.commit()
    return device


def new_code(db: Session, outlet_id: str | None, device_id: str) -> tuple[Device, str]:
    """The old token is cancelled and the device waits again, so a lost or replaced tablet must be paired anew."""
    device = _find(db, outlet_id, device_id)
    device.token_hash = None
    device.status = WAITING_STATUS
    device.paired_at = None
    print_routing.sync_used(db, device.outlet_id)
    return device, _issue_code(db, device)


def revoke(db: Session, outlet_id: str | None, device_id: str) -> None:
    device = _find(db, outlet_id, device_id)
    db.delete(device)
    db.flush()
    print_routing.sync_used(db, device.outlet_id)
    db.commit()


def _issue_code(db: Session, device: Device) -> str:
    code = codes.new_code()
    device.code_hash = hash_token(codes.normalise(code))
    device.code_expires_at = now() + CODE_VALID_FOR
    db.commit()
    return code


def _find(db: Session, outlet_id: str | None, device_id: str) -> Device:
    device = db.get(Device, device_id)
    if device is None or (outlet_id and device.outlet_id != outlet_id):
        raise DomainError(messages.NOT_FOUND, status=NOT_FOUND)
    return device
