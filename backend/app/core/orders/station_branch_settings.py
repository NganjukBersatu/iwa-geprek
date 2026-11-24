"""Pengaturan stasiun per cabang: membaca semuanya sekaligus, kategori per cabang, menyalin ke cabang pilihan, dan bawaan untuk cabang baru."""
from dataclasses import dataclass

from sqlalchemy import delete, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.catalog.menu import CATEGORY_KIND
from app.core.errors import DomainError
from app.core.orders import station_setup
from app.models.category import Category
from app.models.outlet import Outlet
from app.models.station import CategoryBranchStation, CategoryStation, Station, StationBranchRole, StationBranchSetting, StationKind, StationRole

NOT_FOUND = 404
MAX_TARGETS = 200
NO_TARGET = "Pilih minimal satu cabang tujuan."
TOO_MANY_TARGETS = "Pilih paling banyak {limit} cabang tujuan."
SAME_BRANCH = "Cabang tujuan tidak boleh sama dengan cabang asal."
CATEGORY_NOT_FOUND = "Kategori tidak ditemukan. Muat ulang halaman, lalu pilih lagi."
TARGET_ONLY_DELIVER = "Target antar hanya untuk stasiun berjenis Mengantar menu."


def _routes(db: Session, outlet_ids: list[str]) -> tuple[dict[str, str], dict[tuple[str, str], str | None]]:
    """Kategori bawaan per kategori dan pengecualian per (cabang, kategori); dua query."""
    defaults = dict(db.execute(select(CategoryStation.category_id, CategoryStation.station_id)).all())
    own = {
        (outlet_id, category_id): station_id
        for outlet_id, category_id, station_id in db.execute(
            select(CategoryBranchStation.outlet_id, CategoryBranchStation.category_id, CategoryBranchStation.station_id).where(CategoryBranchStation.outlet_id.in_(outlet_ids))
        ).all()
    }
    return defaults, own


def copy_to_branches(db: Session, station_id: str, from_outlet_id: str, to_outlet_ids: list[str]) -> None:
    """Pengingat, target antar, peran cabang, dan arah kategori stasiun ini di cabang tujuan dibuat sama dengan cabang asal; pemanggil yang menyimpan."""
    targets = list(dict.fromkeys(to_outlet_ids))
    if not targets:
        raise DomainError(NO_TARGET)
    if len(targets) > MAX_TARGETS:
        raise DomainError(TOO_MANY_TARGETS.format(limit=MAX_TARGETS))
    if from_outlet_id in targets:
        raise DomainError(SAME_BRANCH)
    if db.get(Outlet, from_outlet_id) is None:
        raise DomainError(station_setup.BRANCH_NOT_FOUND, status=NOT_FOUND)
    source = station_setup.branch_choices(db, station_id, [from_outlet_id])[from_outlet_id]
    station_setup.set_station_branches(
        db,
        station_id,
        [station_setup.BranchChange(outlet_id, source.target_seconds, source.reminder_seconds, source.role_ids) for outlet_id in targets],
    )
    defaults, own = _routes(db, [from_outlet_id, *targets])
    category_ids = list(db.scalars(select(Category.id).where(Category.kind == CATEGORY_KIND).order_by(Category.id)).all())

    def effective(outlet_id: str, category_id: str) -> str | None:
        return own[(outlet_id, category_id)] if (outlet_id, category_id) in own else defaults.get(category_id)

    follow: list[tuple[str, str]] = []
    override: list[dict[str, str | None]] = []
    for outlet_id in sorted(targets):
        for category_id in category_ids:
            wanted = effective(from_outlet_id, category_id)
            current = effective(outlet_id, category_id)
            # Hanya kategori yang menyangkut stasiun ini yang disamakan; kategori stasiun lain di cabang tujuan tidak disentuh.
            if wanted == current or station_id not in (wanted, current):
                continue
            if wanted == defaults.get(category_id):
                follow.append((outlet_id, category_id))
            else:
                override.append({"outlet_id": outlet_id, "category_id": category_id, "station_id": wanted})
    if follow:
        db.execute(delete(CategoryBranchStation).where(tuple_(CategoryBranchStation.outlet_id, CategoryBranchStation.category_id).in_(follow)))
    if override:
        statement = insert(CategoryBranchStation).values(override)
        db.execute(statement.on_conflict_do_update(index_elements=["outlet_id", "category_id"], set_={"station_id": statement.excluded.station_id}))
    db.flush()


@dataclass(frozen=True)
class BranchSettings:
    """Pengaturan satu stasiun di satu cabang beserta peran bawaannya, untuk halaman detail tablet."""

    station_id: str
    reminder_seconds: int
    target_seconds: int | None
    # Peran milik cabang ini; kosong berarti ikut default_role_ids.
    role_ids: list[str]
    default_role_ids: list[str]
    category_ids: list[str]


def settings_of_branch(db: Session, outlet_id: str) -> list[BranchSettings]:
    """Semua stasiun di satu cabang dalam enam query, berapa pun jumlah stasiunnya."""
    stations = list(db.scalars(select(Station.id).order_by(Station.position, Station.name, Station.id)).all())
    rows = {row.station_id: row for row in db.scalars(select(StationBranchSetting).where(StationBranchSetting.outlet_id == outlet_id)).all()}
    own_roles: dict[str, list[str]] = {}
    for station_id, role_id in db.execute(select(StationBranchRole.station_id, StationBranchRole.role_id).where(StationBranchRole.outlet_id == outlet_id).order_by(StationBranchRole.role_id)).all():
        own_roles.setdefault(station_id, []).append(role_id)
    default_roles: dict[str, list[str]] = {}
    for station_id, role_id in db.execute(select(StationRole.station_id, StationRole.role_id).order_by(StationRole.role_id)).all():
        default_roles.setdefault(station_id, []).append(role_id)
    categories = branch_categories(db, outlet_id)
    return [
        BranchSettings(
            station_id,
            rows[station_id].reminder_seconds if station_id in rows else station_setup.REMINDER_DEFAULT_SECONDS,
            rows[station_id].target_seconds if station_id in rows else None,
            own_roles.get(station_id, []),
            default_roles.get(station_id, []),
            categories.get(station_id, []),
        )
        for station_id in stations
    ]


def branch_categories(db: Session, outlet_id: str) -> dict[str, list[str]]:
    """Kategori yang dibuat di tiap stasiun di satu cabang, setelah pengecualian cabang; dua query."""
    defaults, own = _routes(db, [outlet_id])
    found: dict[str, list[str]] = {}
    for category_id in db.scalars(select(Category.id).where(Category.kind == CATEGORY_KIND).order_by(Category.name, Category.id)).all():
        station_id = own[(outlet_id, category_id)] if (outlet_id, category_id) in own else defaults.get(category_id)
        if station_id:
            found.setdefault(station_id, []).append(category_id)
    return found


def set_branch_categories(db: Session, outlet_id: str, station_id: str, category_ids: list[str]) -> None:
    """Kategori stasiun pembuat ini di satu cabang menjadi tepat daftar ini; yang dilepas kembali ke bawaannya, atau tanpa stasiun bila bawaannya stasiun ini."""
    station = db.get(Station, station_id)
    if station is None:
        raise DomainError(station_setup.STATION_NOT_FOUND, status=NOT_FOUND)
    if station.kind != StationKind.MAKE:
        raise DomainError(station_setup.NOT_A_MAKER)
    wanted = set(category_ids)
    if wanted:
        known = set(db.scalars(select(Category.id).where(Category.id.in_(list(wanted)), Category.kind == CATEGORY_KIND)).all())
        if known != wanted:
            raise DomainError(CATEGORY_NOT_FOUND, status=NOT_FOUND)
    defaults, own = _routes(db, [outlet_id])
    current = set(branch_categories(db, outlet_id).get(station_id, []))
    follow: list[str] = []
    override: list[dict[str, str | None]] = []
    for category_id in sorted(wanted - current):
        if defaults.get(category_id) == station_id:
            follow.append(category_id)
        else:
            override.append({"outlet_id": outlet_id, "category_id": category_id, "station_id": station_id})
    for category_id in sorted(current - wanted):
        if defaults.get(category_id) != station_id:
            follow.append(category_id)
        else:
            override.append({"outlet_id": outlet_id, "category_id": category_id, "station_id": None})
    if follow:
        db.execute(delete(CategoryBranchStation).where(CategoryBranchStation.outlet_id == outlet_id, CategoryBranchStation.category_id.in_(follow)))
    if override:
        statement = insert(CategoryBranchStation).values(override)
        db.execute(statement.on_conflict_do_update(index_elements=["outlet_id", "category_id"], set_={"station_id": statement.excluded.station_id}))
    db.flush()


@dataclass(frozen=True)
class Defaults:
    """Bawaan satu stasiun untuk cabang yang belum mengatur sendiri; category_ids None berarti kategori tidak diubah."""

    role_ids: tuple[str, ...]
    # Target antar hanya untuk stasiun Mengantar menu; changes_target salah berarti target tidak diubah.
    changes_target: bool
    target_seconds: int | None
    category_ids: list[str] | None


def set_defaults(db: Session, station_id: str, defaults: Defaults) -> None:
    """Peran, target antar, dan kategori bawaan stasiun ini diganti bersama; pemanggil yang menyimpan dalam satu transaksi."""
    station = db.get(Station, station_id)
    if station is None:
        raise DomainError(station_setup.STATION_NOT_FOUND, status=NOT_FOUND)
    if defaults.changes_target and station.kind != StationKind.DELIVER:
        raise DomainError(TARGET_ONLY_DELIVER)
    if defaults.category_ids is not None and station.kind != StationKind.MAKE:
        raise DomainError(station_setup.NOT_A_MAKER)
    station_setup.set_station_roles(db, station.id, defaults.role_ids)
    if defaults.changes_target:
        station_setup.update_station(db, station.id, station.name, station.kind, defaults.target_seconds)
    if defaults.category_ids is not None:
        _set_default_categories(db, station, defaults.category_ids)
    db.flush()


def _set_default_categories(db: Session, station: Station, category_ids: list[str]) -> None:
    """Kategori bawaan stasiun pembuat ini untuk cabang yang tidak mengatur sendiri; kategori yang dilepas tidak lagi punya stasiun bawaan."""
    wanted = sorted(set(category_ids))
    if wanted:
        known = set(db.scalars(select(Category.id).where(Category.id.in_(wanted), Category.kind == CATEGORY_KIND)).all())
        if known != set(wanted):
            raise DomainError(CATEGORY_NOT_FOUND, status=NOT_FOUND)
    db.execute(delete(CategoryStation).where(CategoryStation.station_id == station.id, CategoryStation.category_id.not_in(wanted)))
    if wanted:
        statement = insert(CategoryStation).values([{"category_id": category_id, "station_id": station.id} for category_id in wanted])
        db.execute(statement.on_conflict_do_update(index_elements=["category_id"], set_={"station_id": station.id}))
    db.flush()
