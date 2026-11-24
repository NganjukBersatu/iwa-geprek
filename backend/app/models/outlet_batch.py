import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.shift_code import ShiftCode
from app.models.user import User


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


KIND_OUTLET = "outlet"
KIND_ROUTINE = "routine"
FILL_ONE = "one"
FILL_EACH = "each"
UNIT_DAY = "day"
UNIT_WEEK = "week"
UNIT_MONTH = "month"
TARGET_SHIFT = "shift"
TARGET_USERS = "users"
# Kunci pengisi untuk tugas yang cukup diisi satu orang; tugas yang diisi tiap orang memakai id stafnya.
SHARED_FILLER = ""
VERSION_FIX = "fix"
VERSION_CANCEL = "cancel"
VERSION_DELETE = "delete"


class OutletBatchShiftCode(Base):
    """Kode shift yang mendapat sebuah tugas rutin; tugas outlet tidak punya baris di sini."""

    __tablename__ = "outlet_batch_shift_codes"

    batch_id: Mapped[str] = mapped_column(String, ForeignKey("outlet_batches.id", ondelete="CASCADE"), primary_key=True)
    shift_code_id: Mapped[str] = mapped_column(String, ForeignKey("shift_codes.id", ondelete="CASCADE"), primary_key=True)


class OutletBatchUser(Base):
    """Orang yang ditunjuk menerima sebuah tugas rutin; hanya terisi bila penerimanya orang tertentu."""

    __tablename__ = "outlet_batch_users"

    batch_id: Mapped[str] = mapped_column(String, ForeignKey("outlet_batches.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


class OutletBatch(Base):
    """Templat tugas berulang satu cabang: tugas outlet untuk siapa pun yang hadir, atau tugas rutin untuk yang dijadwalkan di kode shiftnya."""

    __tablename__ = "outlet_batches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    outlet_id: Mapped[str] = mapped_column(String, ForeignKey("outlets.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(Text, default=KIND_OUTLET, server_default=KIND_OUTLET)
    fill_mode: Mapped[str] = mapped_column(Text, default=FILL_ONE, server_default=FILL_ONE)
    target: Mapped[str] = mapped_column(Text, default=TARGET_SHIFT, server_default=TARGET_SHIFT)
    name: Mapped[str] = mapped_column(String(100))
    start_clock: Mapped[str] = mapped_column(String(5))
    end_clock: Mapped[str] = mapped_column(String(5))
    # Pola lama, hanya dibaca: hari dalam minggu (Senin 0) berjajar dengan koma, kosong berarti tiap hari; dipakai selama [repeat_unit] kosong.
    weekdays: Mapped[str | None] = mapped_column(String(13), nullable=True)
    # Satuan pola berulang; kosong hanya pada templat lama yang belum disimpan ulang.
    repeat_unit: Mapped[str | None] = mapped_column(Text, nullable=True)
    repeat_every: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    # Hari pertama tugas berlaku, sekaligus patokan hari atau tanggal pengulangannya.
    starts_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)

    items: Mapped[list["OutletBatchItem"]] = relationship(
        "OutletBatchItem",
        order_by="OutletBatchItem.position",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    shift_codes: Mapped[list[ShiftCode]] = relationship(
        ShiftCode,
        secondary="outlet_batch_shift_codes",
        order_by=(ShiftCode.sort_order, ShiftCode.code),
        lazy="selectin",
    )

    assigned_user: Mapped[list[User]] = relationship(
        User,
        secondary="outlet_batch_users",
        order_by=(User.name, User.username),
        lazy="selectin",
    )

    @property
    def for_named_user(self) -> bool:
        return self.target == TARGET_USERS

    @property
    def recipients(self) -> list[User]:
        """Penerima yang masih berlaku: yang dinonaktifkan atau pindah cabang lepas dengan sendirinya tanpa perlu dibersihkan."""
        return [person for person in self.assigned_user if person.is_active and person.outlet_id == self.outlet_id]

    @property
    def each_fills(self) -> bool:
        return self.fill_mode == FILL_EACH

    def filler_key(self, user_id: str) -> str:
        return user_id if self.each_fills else SHARED_FILLER


class OutletBatchItem(Base):
    __tablename__ = "outlet_batch_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    batch_id: Mapped[str] = mapped_column(String, ForeignKey("outlet_batches.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(10))
    required: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    position: Mapped[int] = mapped_column(Integer, default=0)


class OutletBatchRun(Base):
    """Satu pengisian pada satu hari: satu per tugas, atau satu per orang untuk tugas yang diisi tiap orang."""

    __tablename__ = "outlet_batch_runs"
    __table_args__ = (
        Index("unique_outlet_batch_runs_batch_id_and_day_and_filler_key", "batch_id", "day", "filler_key", unique=True),
        Index("index_outlet_batch_runs_on_day", "day"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    batch_id: Mapped[str] = mapped_column(String, ForeignKey("outlet_batches.id", ondelete="CASCADE"))
    day: Mapped[date] = mapped_column(Date)
    filler_key: Mapped[str] = mapped_column(String(64), default=SHARED_FILLER, server_default=SHARED_FILLER)
    completed_by_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    # Terisi saat pengisian dibatalkan atau dihapus; barisnya tetap ada supaya jejaknya tidak hilang, dan dipakai lagi bila tugasnya diisi ulang.
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    completer: Mapped[User | None] = relationship(
        User, primaryjoin="foreign(OutletBatchRun.completed_by_id) == User.id", lazy="selectin"
    )


class OutletBatchRunVersion(Base):
    """Isi sebuah pengisian sebelum diperbaiki atau dibatalkan; penghapusan hanya meninggalkan catatan tanpa isi."""

    __tablename__ = "outlet_batch_run_versions"
    __table_args__ = (Index("unique_outlet_batch_run_versions_run_id_and_number", "run_id", "number", unique=True),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("outlet_batch_runs.id", ondelete="CASCADE"))
    number: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(10))
    answers: Mapped[list[dict[str, str | None]]] = mapped_column(JSONB)
    completed_by_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    changed_by_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class OutletBatchAnswer(Base):
    """The label and kind are copied so the record still reads right after an admin edits the outlet task."""

    __tablename__ = "outlet_batch_answers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("outlet_batch_runs.id", ondelete="CASCADE"))
    item_id: Mapped[str | None] = mapped_column(String, ForeignKey("outlet_batch_items.id", ondelete="SET NULL"), nullable=True)
    item_label: Mapped[str] = mapped_column(String(200))
    item_kind: Mapped[str] = mapped_column(String(10))
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
