from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Integer, SmallInteger, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

GENERATED_ID = text("gen_random_uuid()::text")


class StationKind(StrEnum):
    MAKE = "make"
    DELIVER = "deliver"
    HANDOVER = "handover"


class Correction(StrEnum):
    ADDED = "added"
    CHANGED = "changed"


class StepKind(StrEnum):
    ARRIVE = "arrive"
    START = "start"
    FINISH = "finish"
    UNDO = "undo"
    ACKNOWLEDGE = "acknowledge"


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[str] = mapped_column(Text, primary_key=True, server_default=GENERATED_ID)
    name: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)
    # Target stasiun pengantar atau penyerah; stasiun pembuat memakai target menu.
    target_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class StationFlow(Base):
    __tablename__ = "station_flows"

    outlet_id: Mapped[str] = mapped_column(Text, primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean)


# Stasiun yang dipegang satu tablet; tablet dengan beberapa stasiun menampilkan satu tab untuk tiap stasiun.
class DeviceStation(Base):
    __tablename__ = "device_stations"

    device_id: Mapped[str] = mapped_column(Text, primary_key=True)
    station_id: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


# Stasiun tanpa tablet yang struk menunya dikirim dari tablet kasir ini ke printer di stasiun itu.
class DeviceStationPrint(Base):
    __tablename__ = "device_station_prints"

    device_id: Mapped[str] = mapped_column(Text, primary_key=True)
    station_id: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class StationRole(Base):
    """Peran jadwal bawaan yang mengerjakan satu stasiun di semua cabang; cabang dengan peran sendiri memakai miliknya."""

    __tablename__ = "station_roles"

    station_id: Mapped[str] = mapped_column(Text, primary_key=True)
    role_id: Mapped[str] = mapped_column(Text, primary_key=True)


class StationBranchSetting(Base):
    __tablename__ = "station_branch_settings"

    outlet_id: Mapped[str] = mapped_column(Text, primary_key=True)
    station_id: Mapped[str] = mapped_column(Text, primary_key=True)
    used: Mapped[bool] = mapped_column(Boolean)
    target_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Jeda bunyi pengingat selama masih ada menu yang menunggu; 0 berarti pengingat mati di stasiun ini.
    reminder_seconds: Mapped[int] = mapped_column(Integer, server_default=text("60"))


class StationBranchRole(Base):
    """Peran jadwal yang boleh mengerjakan satu stasiun di satu cabang."""

    __tablename__ = "station_branch_roles"

    outlet_id: Mapped[str] = mapped_column(Text, primary_key=True)
    station_id: Mapped[str] = mapped_column(Text, primary_key=True)
    role_id: Mapped[str] = mapped_column(Text, primary_key=True)


class CategoryStation(Base):
    __tablename__ = "category_stations"

    category_id: Mapped[str] = mapped_column(Text, primary_key=True)
    station_id: Mapped[str] = mapped_column(Text)


class CategoryBranchStation(Base):
    __tablename__ = "category_branch_stations"

    outlet_id: Mapped[str] = mapped_column(Text, primary_key=True)
    category_id: Mapped[str] = mapped_column(Text, primary_key=True)
    # Kosong berarti cabang ini tidak membuat kategori itu di stasiun mana pun.
    station_id: Mapped[str | None] = mapped_column(Text, nullable=True)


class MenuTarget(Base):
    __tablename__ = "menu_targets"

    menu_item_id: Mapped[str] = mapped_column(Text, primary_key=True)
    target_seconds: Mapped[int] = mapped_column(Integer)


class MenuBranchTarget(Base):
    __tablename__ = "menu_branch_targets"

    outlet_id: Mapped[str] = mapped_column(Text, primary_key=True)
    menu_item_id: Mapped[str] = mapped_column(Text, primary_key=True)
    target_seconds: Mapped[int] = mapped_column(Integer)


class StationTask(Base):
    __tablename__ = "station_tasks"

    id: Mapped[str] = mapped_column(Text, primary_key=True, server_default=GENERATED_ID)
    order_id: Mapped[str] = mapped_column(Text)
    # Kosong setelah koreksi menghapus barisnya; tugas tetap ada supaya stasiun diberi tahu.
    order_item_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    outlet_id: Mapped[str] = mapped_column(Text)
    station_id: Mapped[str] = mapped_column(Text)
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Disalin saat mulai, supaya target yang diubah kemudian tidak mengubah keterlambatan lama.
    target_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correction: Mapped[str | None] = mapped_column(Text, nullable=True)
    removed_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Penundaan menu: sampai kapan, alasan yang diketik karyawan, dan siapa yang menunda; ketiganya terisi bersama atau kosong bersama.
    held_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hold_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    held_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    printed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    __mapper_args__ = {"version_id_col": version}


class StationTaskStep(Base):
    __tablename__ = "station_task_steps"

    id: Mapped[str] = mapped_column(Text, primary_key=True, server_default=GENERATED_ID)
    task_id: Mapped[str] = mapped_column(Text)
    step: Mapped[str] = mapped_column(Text)
    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    intervened: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StationUserStat(Base):
    __tablename__ = "station_user_stats"

    id: Mapped[str] = mapped_column(Text, primary_key=True, server_default=GENERATED_ID)
    outlet_id: Mapped[str] = mapped_column(Text)
    business_day: Mapped[date] = mapped_column(Date)
    hour: Mapped[int] = mapped_column(SmallInteger)
    station_id: Mapped[str] = mapped_column(Text)
    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    tasks: Mapped[int] = mapped_column(Integer)
    wait_seconds: Mapped[int] = mapped_column(BigInteger)
    work_seconds: Mapped[int] = mapped_column(BigInteger)
    targeted: Mapped[int] = mapped_column(Integer)
    on_time: Mapped[int] = mapped_column(Integer)


class StationMenuStat(Base):
    __tablename__ = "station_menu_stats"

    id: Mapped[str] = mapped_column(Text, primary_key=True, server_default=GENERATED_ID)
    outlet_id: Mapped[str] = mapped_column(Text)
    business_day: Mapped[date] = mapped_column(Date)
    hour: Mapped[int] = mapped_column(SmallInteger)
    station_id: Mapped[str] = mapped_column(Text)
    # Kosong setelah menunya dihapus; nama salinan tetap terbaca di laporan.
    menu_item_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    menu_name: Mapped[str] = mapped_column(Text)
    tasks: Mapped[int] = mapped_column(Integer)
    wait_seconds: Mapped[int] = mapped_column(BigInteger)
    work_seconds: Mapped[int] = mapped_column(BigInteger)
    targeted: Mapped[int] = mapped_column(Integer)
    on_time: Mapped[int] = mapped_column(Integer)
