"""Stasiun yang ditetapkan ke tiap tablet: satu pintu untuk papan tablet, hak transaksi, dan tab Perangkat di halaman Cabang web."""
from sqlalchemy import delete, exists, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.models.device import REGISTERED, Device
from app.models.station import DeviceStation, Station, StationKind

CASHIER_SECTION = "kasir"
OTHER_SECTION = "lainnya"
MAX_STATIONS = 50
NOT_FOUND = 404
STATION_NOT_FOUND = "Stasiun tidak ditemukan. Muat ulang halaman, lalu pilih lagi."
TOO_MANY = "Pilih paling banyak {limit} stasiun."
NO_STATION = "Pilih minimal satu stasiun supaya perangkat ini punya tab kerja."


def held_ids(db: Session, device_ids: list[str]) -> dict[str, list[str]]:
    """Stasiun yang dipegang tiap tablet, urut posisi stasiun."""
    if not device_ids:
        return {}
    found: dict[str, list[str]] = {}
    for device_id, station_id in db.execute(
        select(DeviceStation.device_id, DeviceStation.station_id)
        .join(Station, Station.id == DeviceStation.station_id)
        .where(DeviceStation.device_id.in_(device_ids))
        .order_by(DeviceStation.device_id, Station.position, Station.name, Station.id)
    ).all():
        found.setdefault(device_id, []).append(station_id)
    return found


def holds_cashier(db: Session, device: Device) -> bool:
    """Hak sesi kas dan transaksi: tablet yang memegang stasiun Kasir, atau tablet bagian Kasir lama selama belum dipindah."""
    if device.section == CASHIER_SECTION:
        return True
    return bool(
        db.scalar(
            select(
                exists().where(
                    DeviceStation.device_id == device.id,
                    DeviceStation.station_id == Station.id,
                    Station.kind == StationKind.HANDOVER,
                )
            )
        )
    )


def set_stations(db: Session, device: Device, station_ids: list[str]) -> None:
    wanted = sorted(set(station_ids))
    if len(wanted) > MAX_STATIONS:
        raise DomainError(TOO_MANY.format(limit=MAX_STATIONS))
    stations = list(db.scalars(select(Station).where(Station.id.in_(wanted))).all()) if wanted else []
    if len(stations) != len(wanted):
        raise DomainError(STATION_NOT_FOUND, status=NOT_FOUND)
    db.execute(delete(DeviceStation).where(DeviceStation.device_id == device.id, DeviceStation.station_id.not_in(wanted)))
    if wanted:
        statement = insert(DeviceStation).values([{"device_id": device.id, "station_id": station_id} for station_id in wanted])
        db.execute(statement.on_conflict_do_nothing(index_elements=["device_id", "station_id"]))
    # Bagian lama ikut stasiun Kasir; selama stasiun Kasir belum ada di data, bagian lama dibiarkan supaya tablet kasir tetap bisa bertransaksi.
    if db.scalar(select(exists().where(Station.kind == StationKind.HANDOVER))):
        device.section = CASHIER_SECTION if any(station.kind == StationKind.HANDOVER for station in stations) else OTHER_SECTION
    db.flush()


def require_stations(station_ids: list[str]) -> None:
    if not station_ids:
        raise DomainError(NO_STATION)


def options(db: Session, outlet_id: str) -> list[tuple[Station, list[str]]]:
    """Semua stasiun beserta tablet terdaftar di cabang yang memegangnya, untuk dialog perangkat."""
    stations = list(db.scalars(select(Station).order_by(Station.position, Station.name, Station.id)).all())
    names: dict[str, list[str]] = {}
    for station_id, name in db.execute(
        select(DeviceStation.station_id, Device.name)
        .join(Device, Device.id == DeviceStation.device_id)
        .where(Device.outlet_id == outlet_id, Device.status == REGISTERED)
        .order_by(Device.name, Device.id)
    ).all():
        names.setdefault(station_id, []).append(name)
    return [(station, names.get(station.id, [])) for station in stations]
