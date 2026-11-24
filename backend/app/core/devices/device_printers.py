"""Printer yang dilaporkan terpasang di tiap tablet; ringkasannya per stasiun dibaca lewat print_routing."""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import now
from app.core.errors import DomainError
from app.models.printer_category import DevicePrinter, DeviceSlot, PrinterConnection
from app.models.station import Station

MAX_NAME_LENGTH = 120
MAX_ADDRESS_LENGTH = 64
MAX_REPORTED = 60
NOT_FOUND = 404
STATION_NOT_FOUND = "Stasiun printer ini sudah tidak ada. Muat ulang aplikasi, lalu pasang ulang printernya."


@dataclass(frozen=True)
class ReportedPrinter:
    slot: DeviceSlot
    name: str
    address: str
    connection: PrinterConnection
    # Terisi untuk slot station dari APK baru: printer milik stasiun itu.
    station_id: str | None = None


def report(db: Session, device_id: str, printers: list[ReportedPrinter]) -> bool:
    """Mengganti laporan tablet dengan keadaan terbarunya; tidak menulis apa pun bila tidak ada yang berubah, supaya layar lain tidak dimuat ulang sia-sia."""
    wanted = {(printer.slot, printer.station_id): printer for printer in printers}
    stations = sorted({station_id for _, station_id in wanted if station_id})
    if stations and len(set(db.scalars(select(Station.id).where(Station.id.in_(stations))).all())) != len(stations):
        raise DomainError(STATION_NOT_FOUND, status=NOT_FOUND)
    rows = {(DeviceSlot(row.printer_slot), row.station_id): row for row in db.scalars(select(DevicePrinter).where(DevicePrinter.device_id == device_id))}
    current = {
        key: ReportedPrinter(slot=key[0], name=row.printer_name, address=row.printer_address, connection=PrinterConnection(row.connection), station_id=row.station_id)
        for key, row in rows.items()
    }
    if current == wanted:
        return False
    for key, row in rows.items():
        if key not in wanted:
            db.delete(row)
    for key, printer in wanted.items():
        if current.get(key) == printer:
            continue
        row = rows.get(key)
        if row is None:
            row = DevicePrinter(device_id=device_id, printer_slot=printer.slot, station_id=printer.station_id)
            db.add(row)
        row.printer_name, row.printer_address, row.connection, row.reported_at = printer.name, printer.address, printer.connection, now()
    db.flush()
    return True
