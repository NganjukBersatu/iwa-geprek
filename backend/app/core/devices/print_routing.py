"""Satu pintu aturan cetak stasiun: printer selalu berada di stasiunnya, dikirim dari tablet stasiun bila ada, selain itu dari tablet kasir.

Stasiun aktif di cabang berarti dipegang tablet terdaftar; stasiun tanpa tablet hanya dicetak bila dicentang di tablet kasir.
"""
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import delete, exists, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.catalog.menu import CATEGORY_KIND
from app.core.errors import DomainError
from app.core.orders import stations as station_tasks
from app.core.orders.station_setup import REMINDER_DEFAULT_SECONDS
from app.models.category import Category
from app.models.device import REGISTERED, Device
from app.models.menu_item import MenuItem
from app.models.outlet import Outlet
from app.models.printer_category import DevicePrinter, DeviceSlot, PrinterCategory, PrinterConnection, PrinterSlot
from app.models.station import CategoryBranchStation, CategoryStation, DeviceStation, DeviceStationPrint, Station, StationBranchSetting, StationKind

NOT_FOUND = 404
STATION_NOT_FOUND = "Stasiun tidak ditemukan. Muat ulang halaman, lalu pilih lagi."
ONLY_MAKERS = "Hanya stasiun berjenis Membuat menu atau Mengantar menu yang bisa dicetak dari perangkat kasir."
PRINTABLE_FROM_CASHIER = (StationKind.MAKE, StationKind.DELIVER)
MENU_NOT_FOUND = "Menu tidak ditemukan. Muat ulang halaman, lalu pilih lagi."
NEEDS_CASHIER = "Stasiun tanpa perangkat hanya bisa dicetak dari perangkat Mode Kasir."


class RouteState(StrEnum):
    UNUSED = "unused"
    PRINTER_MISSING = "printer_missing"
    PRINTER_DISCONNECTED = "printer_disconnected"
    READY = "ready"


@dataclass(frozen=True)
class Sender:
    device_id: str
    name: str


@dataclass(frozen=True)
class ReportedPrinter:
    name: str
    connected: bool


@dataclass(frozen=True)
class StationRoute:
    station: Station
    # Tablet terdaftar yang memegang stasiun ini dan menampilkan layarnya.
    holders: list[Sender]
    # Tablet yang mengirim struk ke printer stasiun ini; kosong bila stasiun ini tidak mencetak atau belum ada pengirim.
    sender: Sender | None
    printer: ReportedPrinter | None
    state: RouteState
    category_names: list[str]


@dataclass(frozen=True)
class PlanStation:
    station_id: str
    name: str
    # Benar bila tablet ini memegang stasiunnya; salah bila hanya mengirim struk dari tablet kasir.
    held: bool
    category_ids: list[str]
    kind: StationKind


@dataclass(frozen=True)
class PrintPlan:
    receipt: bool
    stations: list[PlanStation]
    mode: str
    # Stasiun tujuan slot Bar dan Dapur APK lama, untuk memindahkan printer yang sudah tersimpan di tablet sekali saja.
    legacy_slots: dict[PrinterSlot, str]


def prints_of(db: Session, device_ids: list[str]) -> dict[str, list[str]]:
    """Stasiun tanpa tablet yang dicetak dari tiap tablet kasir, urut posisi stasiun."""
    if not device_ids:
        return {}
    found: dict[str, list[str]] = {}
    for device_id, station_id in db.execute(
        select(DeviceStationPrint.device_id, DeviceStationPrint.station_id)
        .join(Station, Station.id == DeviceStationPrint.station_id)
        .where(DeviceStationPrint.device_id.in_(device_ids))
        .order_by(DeviceStationPrint.device_id, Station.position, Station.name, Station.id)
    ).all():
        found.setdefault(device_id, []).append(station_id)
    return found


def set_prints(db: Session, device: Device, held_station_ids: list[str], station_ids: list[str]) -> None:
    """Mengganti stasiun tanpa tablet yang dicetak dari tablet ini; stasiun yang dipegangnya sendiri diabaikan karena sudah dicetak di sini."""
    wanted = sorted(set(station_ids) - set(held_station_ids))
    if wanted:
        stations = list(db.scalars(select(Station).where(Station.id.in_(wanted))).all())
        if len(stations) != len(wanted):
            raise DomainError(STATION_NOT_FOUND, status=NOT_FOUND)
        if any(station.kind not in PRINTABLE_FROM_CASHIER for station in stations):
            raise DomainError(ONLY_MAKERS)
        if not holds_cashier(db, held_station_ids):
            raise DomainError(NEEDS_CASHIER)
    db.execute(delete(DeviceStationPrint).where(DeviceStationPrint.device_id == device.id, DeviceStationPrint.station_id.not_in(wanted)))
    if wanted:
        statement = insert(DeviceStationPrint).values([{"device_id": device.id, "station_id": station_id} for station_id in wanted])
        db.execute(statement.on_conflict_do_nothing(index_elements=["device_id", "station_id"]))
    db.flush()


def holds_cashier(db: Session, station_ids: list[str]) -> bool:
    if not station_ids:
        return False
    return bool(db.scalar(select(exists().where(Station.id.in_(station_ids), Station.kind == StationKind.HANDOVER))))


def sync_used(db: Session, outlet_id: str) -> None:
    """Menyelaraskan stasiun aktif cabang dengan tablet terdaftar yang memegangnya; dipanggil setiap tablet, stasiunnya, atau statusnya berubah."""
    # Sesi tidak menyiram otomatis, jadi perubahan tablet yang belum ditulis harus sampai ke database dulu sebelum dibaca di bawah.
    db.flush()
    # Dikunci supaya dua perubahan tablet di cabang yang sama tidak saling menimpa hasil hitungnya.
    db.execute(select(Outlet.id).where(Outlet.id == outlet_id).with_for_update())
    held = set(
        db.scalars(
            select(DeviceStation.station_id)
            .join(Device, Device.id == DeviceStation.device_id)
            .where(Device.outlet_id == outlet_id, Device.status == REGISTERED)
        ).all()
    )
    current = {row.station_id: row for row in db.scalars(select(StationBranchSetting).where(StationBranchSetting.outlet_id == outlet_id)).all()}
    for station_id in db.scalars(select(Station.id).order_by(Station.id)).all():
        used = station_id in held
        row = current.get(station_id)
        if row is None:
            if used:
                db.add(StationBranchSetting(outlet_id=outlet_id, station_id=station_id, used=True, target_seconds=None, reminder_seconds=REMINDER_DEFAULT_SECONDS))
            continue
        if row.used != used:
            row.used = used
    db.flush()
    # Stasiun yang kehilangan tablet tidak punya layar lagi, jadi menu yang menunggu di sana dihentikan dalam transaksi yang sama.
    station_tasks.stop_orphans(db, outlet_id)


def _categories(db: Session, outlet_id: str) -> dict[str, list[tuple[str, str]]]:
    """Kategori menu yang menuju tiap stasiun di cabang ini, dengan pengecualian cabang lebih dulu; nilainya (id, nama) urut nama."""
    defaults = dict(db.execute(select(CategoryStation.category_id, CategoryStation.station_id)).all())
    own = dict(db.execute(select(CategoryBranchStation.category_id, CategoryBranchStation.station_id).where(CategoryBranchStation.outlet_id == outlet_id)).all())
    found: dict[str, list[tuple[str, str]]] = {}
    for category_id, name in db.execute(select(Category.id, Category.name).where(Category.kind == CATEGORY_KIND).order_by(Category.name, Category.id)).all():
        station_id = own[category_id] if category_id in own else defaults.get(category_id)
        if station_id:
            found.setdefault(station_id, []).append((category_id, name))
    return found


def _devices(db: Session, outlet_id: str) -> list[Device]:
    return list(db.scalars(select(Device).where(Device.outlet_id == outlet_id, Device.status == REGISTERED).order_by(Device.name, Device.id)).all())


def _holders(db: Session, devices: list[Device]) -> dict[str, list[Device]]:
    by_id = {device.id: device for device in devices}
    found: dict[str, list[Device]] = {}
    if not by_id:
        return found
    for device_id, station_id in db.execute(
        select(DeviceStation.device_id, DeviceStation.station_id).where(DeviceStation.device_id.in_(list(by_id))).order_by(DeviceStation.station_id)
    ).all():
        found.setdefault(station_id, []).append(by_id[device_id])
    for holders in found.values():
        holders.sort(key=lambda device: (device.name, device.id))
    return found


def legacy_slots(db: Session, outlet_id: str) -> dict[PrinterSlot, str]:
    """Slot Bar atau Dapur APK lama yang semua kategorinya menuju satu stasiun, beserta stasiun itu."""
    by_category = {category_id: station_id for station_id, entries in _categories(db, outlet_id).items() for category_id, _ in entries}
    seen: dict[PrinterSlot, set[str]] = {}
    for category_id, slot in db.execute(select(PrinterCategory.category_id, PrinterCategory.printer_slot).where(PrinterCategory.outlet_id == outlet_id)).all():
        station_id = by_category.get(category_id)
        if station_id:
            seen.setdefault(PrinterSlot(slot), set()).add(station_id)
    return {slot: next(iter(ids)) for slot, ids in seen.items() if len(ids) == 1}


def _printer_for(rows: list[DevicePrinter], station_id: str | None, legacy: PrinterSlot | None, holds_only: bool) -> DevicePrinter | None:
    """Laporan printer satu stasiun di satu tablet; laporan APK lama dipetakan lewat slot lamanya."""
    for row in rows:
        if station_id is None and row.printer_slot == DeviceSlot.RECEIPT:
            return row
        if station_id is not None and row.station_id == station_id:
            return row
    if station_id is None:
        return None
    for row in rows:
        if row.station_id is None and legacy is not None and row.printer_slot == legacy.value:
            return row
        # Slot stasiun APK lama tanpa ID hanya pasti milik stasiun ini bila tablet itu memegang satu stasiun pembuat.
        if row.station_id is None and holds_only and row.printer_slot == DeviceSlot.STATION:
            return row
    return None


def routes(db: Session, outlet_id: str) -> list[StationRoute]:
    """Setiap stasiun di cabang: siapa memegangnya, siapa mengirim struknya, dan keadaan printernya."""
    stations = list(db.scalars(select(Station).order_by(Station.position, Station.name, Station.id)).all())
    devices = _devices(db, outlet_id)
    holders = _holders(db, devices)
    cashiers = {device.id for station in stations if station.kind == StationKind.HANDOVER for device in holders.get(station.id, [])}
    prints = prints_of(db, sorted(cashiers))
    printers: dict[str, list[DevicePrinter]] = {}
    if devices:
        for row in db.scalars(select(DevicePrinter).where(DevicePrinter.device_id.in_([device.id for device in devices]))).all():
            printers.setdefault(row.device_id, []).append(row)
    makers_held = {device.id: sum(1 for station in stations if station.kind == StationKind.MAKE and device in holders.get(station.id, [])) for device in devices}
    legacy_by_station = {station_id: slot for slot, station_id in legacy_slots(db, outlet_id).items()}
    categories = _categories(db, outlet_id)
    found: list[StationRoute] = []
    for station in stations:
        own = holders.get(station.id, [])
        shown = [_sender(device) for device in own]
        names = [name for _, name in categories.get(station.id, [])]
        if station.kind == StationKind.DELIVER:
            if own:
                found.append(StationRoute(station, shown, None, None, RouteState.READY, names))
                continue
            sender = next((device for device in devices if station.id in prints.get(device.id, [])), None)
            row = _printer_for(printers.get(sender.id, []), station.id, None, False) if sender else None
            # Pengantar yang dicetak dari kasir baru aktif setelah printernya tersambung; sebelum itu tidak ada peringatan.
            if row is None or row.connection != PrinterConnection.CONNECTED:
                found.append(StationRoute(station, shown, None, None, RouteState.UNUSED, names))
                continue
            found.append(StationRoute(station, shown, _sender(sender), ReportedPrinter(row.printer_name, True), RouteState.READY, names))
            continue
        sender = own[0] if own else None
        if sender is None and station.kind == StationKind.MAKE:
            sender = next((device for device in devices if station.id in prints.get(device.id, [])), None)
        if sender is None:
            found.append(StationRoute(station, shown, None, None, RouteState.UNUSED, names))
            continue
        row = _printer_for(
            printers.get(sender.id, []),
            None if station.kind == StationKind.HANDOVER else station.id,
            legacy_by_station.get(station.id),
            makers_held.get(sender.id, 0) == 1,
        )
        printer = ReportedPrinter(row.printer_name, row.connection == PrinterConnection.CONNECTED) if row else None
        if printer is None:
            state = RouteState.PRINTER_MISSING
        elif not printer.connected:
            state = RouteState.PRINTER_DISCONNECTED
        else:
            state = RouteState.READY
        found.append(StationRoute(station, shown, _sender(sender), printer, state, names))
    return found


def _sender(device: Device) -> Sender:
    return Sender(device_id=device.id, name=device.name)


def plan_for(db: Session, device: Device) -> PrintPlan:
    """Yang dicetak tablet ini: struk pembayaran bila memegang Kasir, setiap stasiun pembuat yang dipegangnya, dan stasiun tanpa tablet yang dicentang di sini."""
    stations = {station.id: station for station in db.scalars(select(Station).order_by(Station.position, Station.name, Station.id)).all()}
    held = set(db.scalars(select(DeviceStation.station_id).where(DeviceStation.device_id == device.id)).all())
    receipt = any(stations[station_id].kind == StationKind.HANDOVER for station_id in held if station_id in stations)
    taken = set(
        db.scalars(
            select(DeviceStation.station_id)
            .join(Device, Device.id == DeviceStation.device_id)
            .where(Device.outlet_id == device.outlet_id, Device.status == REGISTERED, Device.id != device.id)
        ).all()
    )
    printed = set(prints_of(db, [device.id]).get(device.id, [])) if receipt else set()
    categories = _categories(db, device.outlet_id)
    plan: list[PlanStation] = []
    for station in stations.values():
        category_ids = [category_id for category_id, _ in categories.get(station.id, [])]
        if station.kind == StationKind.MAKE and station.id in held:
            plan.append(PlanStation(station.id, station.name, True, category_ids, station.kind))
        elif station.kind in PRINTABLE_FROM_CASHIER and station.id in printed and station.id not in taken:
            # Stasiun pengantar tidak punya kategori: struk antarnya memuat seluruh pesanan.
            plan.append(PlanStation(station.id, station.name, False, category_ids if station.kind == StationKind.MAKE else [], station.kind))
    return PrintPlan(receipt=receipt, stations=plan, mode=device.mode, legacy_slots=legacy_slots(db, device.outlet_id))


def has_cashier(db: Session, outlet_id: str) -> bool:
    return bool(
        db.scalar(
            select(
                exists().where(
                    DeviceStation.device_id == Device.id,
                    Device.outlet_id == outlet_id,
                    Device.status == REGISTERED,
                    DeviceStation.station_id == Station.id,
                    Station.kind == StationKind.HANDOVER,
                )
            )
        )
    )


@dataclass(frozen=True)
class MenuRoute:
    menu_name: str
    category_name: str | None
    # Kosong bila kategorinya tidak menuju stasiun mana pun di cabang ini, jadi menu langsung diantar tanpa struk stasiun.
    route: StationRoute | None


def route_of_menu(db: Session, outlet_id: str, menu_id: str) -> MenuRoute:
    """Ke mana satu menu masuk di cabang ini: kategori, stasiun, tablet, dan printer, dari aturan yang sama dengan tablet."""
    row = db.execute(select(MenuItem.name, Category.id, Category.name).outerjoin(Category, Category.id == MenuItem.category_id).where(MenuItem.id == menu_id)).first()
    if row is None:
        raise DomainError(MENU_NOT_FOUND, status=NOT_FOUND)
    menu_name, category_id, category_name = row
    station_id = next((station for station, entries in _categories(db, outlet_id).items() if any(entry_id == category_id for entry_id, _ in entries)), None)
    route = next((entry for entry in routes(db, outlet_id) if entry.station.id == station_id), None) if station_id else None
    return MenuRoute(menu_name=menu_name, category_name=category_name, route=route)
