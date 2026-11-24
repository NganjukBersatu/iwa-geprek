from dataclasses import dataclass

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.core.catalog.menu import CATEGORY_KIND
from app.core.errors import DomainError
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.outlet import Outlet
from app.models.role import Role
from app.models.station import (
    CategoryBranchStation,
    CategoryStation,
    MenuBranchTarget,
    MenuTarget,
    Station,
    StationBranchRole,
    StationBranchSetting,
    StationKind,
    StationRole,
    StationTask,
)

PERMISSION_MANAGE = "stasiun.kelola"
MAX_TARGET_SECONDS = 24 * 60 * 60
REMINDER_DEFAULT_SECONDS = 60
REMINDER_MIN_SECONDS = 15
REMINDER_MAX_SECONDS = 10 * 60
MAX_NAME_LENGTH = 40
NOT_FOUND = 404
CONFLICT = 409

STATION_NOT_FOUND = "Stasiun tidak ditemukan."
CATEGORY_NOT_FOUND = "Kategori tidak ditemukan."
MENU_NOT_FOUND = "Menu tidak ditemukan."
NAME_REQUIRED = "Isi nama stasiun."
NAME_TAKEN = "Nama stasiun itu sudah dipakai. Gunakan nama lain."
KIND_TAKEN = "Hanya boleh ada satu stasiun dengan jenis ini."
KIND_LOCKED = "Jenis stasiun yang sudah pernah dipakai tidak bisa diubah, supaya riwayatnya tetap terbaca."
STATION_IN_USE = "Stasiun yang sudah pernah dipakai atau masih dituju kategori tidak bisa dihapus. Lepaskan dari tablet di cabang bila tidak dipakai lagi."
NOT_A_MAKER = "Kategori menu hanya bisa diarahkan ke stasiun berjenis Membuat menu."
TARGET_RANGE = "Isi target antara 1 detik dan 24 jam."
REMINDER_RANGE = "Isi jeda pengingat 0 untuk mematikan, atau antara 15 detik dan 10 menit."
BRANCH_NOT_FOUND = "Cabang tidak ditemukan. Muat ulang halaman, lalu coba lagi."
BRANCH_TWICE = "Setiap cabang hanya boleh dikirim sekali."
ROLE_NOT_FOUND = "Peran tidak ditemukan. Muat ulang halaman, lalu coba lagi."


@dataclass(frozen=True)
class BranchStation:
    station: Station
    used: bool
    target_seconds: int | None
    reminder_seconds: int = REMINDER_DEFAULT_SECONDS


@dataclass(frozen=True)
class BranchSetup:
    outlet_id: str
    stations: dict[str, BranchStation]

    def used(self, station_id: str | None) -> BranchStation | None:
        found = self.stations.get(station_id or "")
        if found is None or not found.used:
            return None
        return found

    def of_kind(self, kind: StationKind) -> BranchStation | None:
        return next((entry for entry in self.stations.values() if entry.used and entry.station.kind == kind), None)

    def maker(self, station_id: str | None) -> BranchStation | None:
        found = self.used(station_id)
        if found is None or found.station.kind != StationKind.MAKE:
            return None
        return found

    def delivery_for(self, order_type: str) -> BranchStation | None:
        # Mengantar ke meja dan menyerahkan pesanan dibawa pulang sama-sama pekerjaan Waiters; Kasir selesai saat pesanan dibayar.
        return self.of_kind(StationKind.DELIVER)


def setup_of(db: Session, outlet_id: str) -> BranchSetup:
    stations = db.scalars(select(Station).order_by(Station.position, Station.name, Station.id)).all()
    own = {row.station_id: row for row in db.scalars(select(StationBranchSetting).where(StationBranchSetting.outlet_id == outlet_id)).all()}
    resolved: dict[str, BranchStation] = {}
    for station in stations:
        row = own.get(station.id)
        resolved[station.id] = BranchStation(
            station=station,
            # Stasiun yang belum diatur di cabang dianggap tidak dipakai, termasuk Kasir.
            used=row.used if row is not None else False,
            target_seconds=row.target_seconds if row is not None and row.target_seconds is not None else station.target_seconds,
            reminder_seconds=row.reminder_seconds if row is not None else REMINDER_DEFAULT_SECONDS,
        )
    return BranchSetup(outlet_id=outlet_id, stations=resolved)


def makers_of_menus(db: Session, outlet_id: str, menu_ids: set[str]) -> dict[str, str | None]:
    if not menu_ids:
        return {}
    rows = db.execute(
        select(MenuItem.id, MenuItem.category_id, CategoryStation.station_id)
        .outerjoin(CategoryStation, CategoryStation.category_id == MenuItem.category_id)
        .where(MenuItem.id.in_(menu_ids))
    ).all()
    category_ids = {category_id for _, category_id, _ in rows if category_id}
    own: dict[str, str | None] = {}
    if category_ids:
        own = dict(
            db.execute(
                select(CategoryBranchStation.category_id, CategoryBranchStation.station_id).where(
                    CategoryBranchStation.outlet_id == outlet_id, CategoryBranchStation.category_id.in_(category_ids)
                )
            ).all()
        )
    return {menu_id: own[category_id] if category_id in own else default for menu_id, category_id, default in rows}


def menu_targets(db: Session, outlet_id: str, menu_ids: set[str]) -> dict[str, int | None]:
    if not menu_ids:
        return {}
    defaults = dict(db.execute(select(MenuTarget.menu_item_id, MenuTarget.target_seconds).where(MenuTarget.menu_item_id.in_(menu_ids))).all())
    own = dict(
        db.execute(
            select(MenuBranchTarget.menu_item_id, MenuBranchTarget.target_seconds).where(
                MenuBranchTarget.outlet_id == outlet_id, MenuBranchTarget.menu_item_id.in_(menu_ids)
            )
        ).all()
    )
    return {menu_id: own.get(menu_id, defaults.get(menu_id)) for menu_id in menu_ids}


def _target(seconds: int | None) -> int | None:
    if seconds is not None and not 1 <= seconds <= MAX_TARGET_SECONDS:
        raise DomainError(TARGET_RANGE)
    return seconds


def _reminder(seconds: int) -> int:
    if seconds != 0 and not REMINDER_MIN_SECONDS <= seconds <= REMINDER_MAX_SECONDS:
        raise DomainError(REMINDER_RANGE)
    return seconds


def _station(db: Session, station_id: str) -> Station:
    found = db.get(Station, station_id)
    if found is None:
        raise DomainError(STATION_NOT_FOUND, status=NOT_FOUND)
    return found


def _checked_name(db: Session, name: str, kind: StationKind, own_id: str | None) -> str:
    clean = name.strip()[:MAX_NAME_LENGTH]
    if not clean:
        raise DomainError(NAME_REQUIRED)
    other = Station.id != (own_id or "")
    if db.scalar(select(exists().where(other, func.lower(Station.name) == clean.lower()))):
        raise DomainError(NAME_TAKEN, status=CONFLICT)
    if kind != StationKind.MAKE and db.scalar(select(exists().where(other, Station.kind == kind))):
        raise DomainError(KIND_TAKEN, status=CONFLICT)
    return clean


def _used_before(db: Session, station_id: str) -> bool:
    return bool(db.scalar(select(exists().where(StationTask.station_id == station_id))))


def create_station(db: Session, name: str, kind: StationKind, target_seconds: int | None) -> Station:
    clean = _checked_name(db, name, kind, None)
    position = (db.scalar(select(func.max(Station.position))) or 0) + 1
    station = Station(name=clean, kind=kind, position=position, target_seconds=_target(target_seconds) if kind == StationKind.DELIVER else None)
    db.add(station)
    db.flush()
    return station


def update_station(db: Session, station_id: str, name: str, kind: StationKind, target_seconds: int | None) -> Station:
    station = _station(db, station_id)
    clean = _checked_name(db, name, kind, station.id)
    if kind != station.kind and _used_before(db, station.id):
        raise DomainError(KIND_LOCKED, status=CONFLICT)
    station.name, station.kind, station.target_seconds = clean, kind, _target(target_seconds) if kind == StationKind.DELIVER else None
    db.flush()
    return station


def delete_station(db: Session, station_id: str) -> None:
    station = _station(db, station_id)
    pointed = db.scalar(select(exists().where(CategoryStation.station_id == station.id))) or db.scalar(
        select(exists().where(CategoryBranchStation.station_id == station.id))
    )
    if pointed or _used_before(db, station.id):
        raise DomainError(STATION_IN_USE, status=CONFLICT)
    db.delete(station)
    db.flush()


@dataclass(frozen=True)
class BranchChoice:
    """Pengaturan stasiun di satu cabang seperti tersimpan; aktif berarti dipegang tablet terdaftar di cabang itu."""

    outlet_id: str
    used: bool
    target_seconds: int | None
    reminder_seconds: int
    # Peran milik cabang ini; kosong berarti ikut peran bawaan stasiun.
    role_ids: tuple[str, ...]


def branch_choices(db: Session, station_id: str, outlet_ids: list[str]) -> dict[str, BranchChoice]:
    """Pengaturan stasiun ini di cabang yang diminta; cabang tanpa baris berarti tidak aktif."""
    _station(db, station_id)
    if not outlet_ids:
        return {}
    rows = db.scalars(select(StationBranchSetting).where(StationBranchSetting.station_id == station_id, StationBranchSetting.outlet_id.in_(outlet_ids))).all()
    own = {row.outlet_id: row for row in rows}
    roles: dict[str, list[str]] = {}
    for role_outlet, role_id in db.execute(
        select(StationBranchRole.outlet_id, StationBranchRole.role_id)
        .where(StationBranchRole.station_id == station_id, StationBranchRole.outlet_id.in_(outlet_ids))
        .order_by(StationBranchRole.role_id)
    ).all():
        roles.setdefault(role_outlet, []).append(role_id)
    return {
        outlet_id: BranchChoice(
            outlet_id,
            own[outlet_id].used if outlet_id in own else False,
            own[outlet_id].target_seconds if outlet_id in own else None,
            own[outlet_id].reminder_seconds if outlet_id in own else REMINDER_DEFAULT_SECONDS,
            tuple(roles.get(outlet_id, ())),
        )
        for outlet_id in outlet_ids
    }


@dataclass(frozen=True)
class BranchChange:
    """Pengaturan stasiun di satu cabang yang boleh diubah admin; aktif tidaknya mengikuti tablet pemegangnya, bukan diisi di sini."""

    outlet_id: str
    target_seconds: int | None
    # None berarti tidak diubah.
    reminder_seconds: int | None = None
    role_ids: tuple[str, ...] | None = None


def set_station_branches(db: Session, station_id: str, choices: list[BranchChange]) -> None:
    """Menyimpan banyak cabang dalam satu transaksi; cabang yang belum punya baris dibuat tidak aktif sampai ada tablet yang memegang stasiunnya."""
    station = _station(db, station_id)
    wanted = {choice.outlet_id: choice for choice in choices}
    if len(wanted) != len(choices):
        raise DomainError(BRANCH_TWICE)
    if not wanted:
        return
    known = set(db.scalars(select(Outlet.id).where(Outlet.id.in_(list(wanted)))).all())
    if known != set(wanted):
        raise DomainError(BRANCH_NOT_FOUND, status=NOT_FOUND)
    rows = {
        row.outlet_id: row
        for row in db.scalars(
            select(StationBranchSetting).where(StationBranchSetting.station_id == station.id, StationBranchSetting.outlet_id.in_(list(wanted))).with_for_update()
        ).all()
    }
    for outlet_id in sorted(wanted):
        choice = wanted[outlet_id]
        row = rows.get(outlet_id)
        if row is None:
            row = StationBranchSetting(outlet_id=outlet_id, station_id=station.id, used=False, reminder_seconds=REMINDER_DEFAULT_SECONDS)
            db.add(row)
        # Hanya stasiun pengantar yang punya target per cabang; pembuat memakai target menu dan Kasir selesai saat dibayar.
        row.target_seconds = _target(choice.target_seconds) if station.kind == StationKind.DELIVER else None
        if choice.reminder_seconds is not None:
            row.reminder_seconds = _reminder(choice.reminder_seconds)
        if choice.role_ids is not None:
            _set_roles(db, outlet_id, station.id, choice.role_ids)
    db.flush()


def _known_roles(db: Session, role_ids: tuple[str, ...]) -> set[str]:
    """Peran yang tidak dikenal ditolak supaya tidak tersimpan diam-diam."""
    wanted = set(role_ids)
    if wanted:
        known = set(db.scalars(select(Role.id).where(Role.id.in_(list(wanted)))).all())
        if known != wanted:
            raise DomainError(ROLE_NOT_FOUND, status=NOT_FOUND)
    return wanted


def station_role_ids(db: Session, station_id: str) -> list[str]:
    _station(db, station_id)
    return list(db.scalars(select(StationRole.role_id).where(StationRole.station_id == station_id).order_by(StationRole.role_id)).all())


def set_station_roles(db: Session, station_id: str, role_ids: tuple[str, ...]) -> None:
    """Mengganti peran bawaan stasiun untuk semua cabang; cabang yang punya peran sendiri tidak terpengaruh."""
    station = _station(db, station_id)
    wanted = _known_roles(db, role_ids)
    current = {row.role_id: row for row in db.scalars(select(StationRole).where(StationRole.station_id == station.id)).all()}
    for role_id, row in current.items():
        if role_id not in wanted:
            db.delete(row)
    for role_id in sorted(wanted - set(current)):
        db.add(StationRole(station_id=station.id, role_id=role_id))
    db.flush()


def _set_roles(db: Session, outlet_id: str, station_id: str, role_ids: tuple[str, ...]) -> None:
    """Mengganti peran yang mengerjakan stasiun di satu cabang; kosong berarti cabang ini memakai peran bawaan stasiun."""
    wanted = _known_roles(db, role_ids)
    current = {row.role_id: row for row in db.scalars(select(StationBranchRole).where(StationBranchRole.outlet_id == outlet_id, StationBranchRole.station_id == station_id)).all()}
    for role_id, row in current.items():
        if role_id not in wanted:
            db.delete(row)
    for role_id in sorted(wanted - set(current)):
        db.add(StationBranchRole(outlet_id=outlet_id, station_id=station_id, role_id=role_id))


def _maker_or_none(db: Session, station_id: str | None) -> str | None:
    if station_id is None:
        return None
    if _station(db, station_id).kind != StationKind.MAKE:
        raise DomainError(NOT_A_MAKER)
    return station_id


def _menu_category(db: Session, category_id: str) -> Category:
    category = db.get(Category, category_id)
    if category is None or category.kind != CATEGORY_KIND:
        raise DomainError(CATEGORY_NOT_FOUND, status=NOT_FOUND)
    return category


def set_category_station(db: Session, category_id: str, station_id: str | None) -> None:
    _menu_category(db, category_id)
    maker = _maker_or_none(db, station_id)
    row = db.get(CategoryStation, category_id)
    if maker is None:
        if row is not None:
            db.delete(row)
        db.flush()
        return
    if row is None:
        row = CategoryStation(category_id=category_id, station_id=maker)
        db.add(row)
    row.station_id = maker
    db.flush()


def set_category_for_branch(db: Session, outlet_id: str, category_id: str, follows_default: bool, station_id: str | None) -> None:
    _menu_category(db, category_id)
    if db.get(Outlet, outlet_id) is None:
        raise DomainError(BRANCH_NOT_FOUND, status=NOT_FOUND)
    row = db.get(CategoryBranchStation, (outlet_id, category_id))
    if follows_default:
        if row is not None:
            db.delete(row)
        db.flush()
        return
    if row is None:
        row = CategoryBranchStation(outlet_id=outlet_id, category_id=category_id)
        db.add(row)
    row.station_id = _maker_or_none(db, station_id)
    db.flush()


def _menu(db: Session, menu_id: str) -> MenuItem:
    menu = db.get(MenuItem, menu_id)
    if menu is None:
        raise DomainError(MENU_NOT_FOUND, status=NOT_FOUND)
    return menu


def set_menu_target(db: Session, menu_id: str, seconds: int | None) -> None:
    _menu(db, menu_id)
    row = db.get(MenuTarget, menu_id)
    if seconds is None:
        if row is not None:
            db.delete(row)
        db.flush()
        return
    if row is None:
        row = MenuTarget(menu_item_id=menu_id, target_seconds=_target(seconds))
        db.add(row)
    row.target_seconds = _target(seconds)
    db.flush()


def set_menu_target_for_branch(db: Session, outlet_id: str, menu_id: str, seconds: int | None) -> None:
    _menu(db, menu_id)
    row = db.get(MenuBranchTarget, (outlet_id, menu_id))
    if seconds is None:
        if row is not None:
            db.delete(row)
        db.flush()
        return
    if row is None:
        row = MenuBranchTarget(outlet_id=outlet_id, menu_item_id=menu_id, target_seconds=_target(seconds))
        db.add(row)
    row.target_seconds = _target(seconds)
    db.flush()
