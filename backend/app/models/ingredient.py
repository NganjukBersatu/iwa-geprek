import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import now
from app.core.database import Base
from app.models.business_day import business_day_column

INGREDIENT_IN = "masuk"
INGREDIENT_OUT = "keluar"
INGREDIENT_WASTE = "rusak"
INGREDIENT_RND = "rnd"
INGREDIENT_ADJUSTMENT = "penyesuaian"
# Kartu stok awal periode: penanda bahan sudah diisi, dicap sedetik sebelum periode dimulai; kartu lama dari web hanya dikenali dari awalan catatannya.
OPENING_CAUSE = "stok_awal"
OPENING_NOTE_PREFIX = "Stok awal "


class CatalogIngredient(Base):
    """The identity (name and unit) one ingredient shares across branches."""

    __tablename__ = "catalog_ingredients"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    unit_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Ingredient(Base):
    """A raw material of one branch, priced per smallest unit."""

    __tablename__ = "ingredients"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    outlet_id: Mapped[str] = mapped_column(String)
    catalog_id: Mapped[str | None] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    unit_id: Mapped[str | None] = mapped_column(String, nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    package_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    package_size: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    shrink_tolerance: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    minimum: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    is_active: Mapped[bool] = mapped_column(Boolean)
    is_available: Mapped[bool] = mapped_column(Boolean)
    # Written only by the database trigger on kartu_bahan, in the same transaction as each card; the app reads it, never sets it.
    balance: Mapped[Decimal] = mapped_column(Numeric(16, 3), server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class IngredientCard(Base):
    """One ingredient movement; the ingredient's balance moves with it through a database trigger."""

    __tablename__ = "ingredient_cards"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    outlet_id: Mapped[str] = mapped_column(String)
    ingredient_id: Mapped[str | None] = mapped_column(String, nullable=True)
    ingredient_name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(20))
    qty: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    expense_id: Mapped[str | None] = mapped_column(String, nullable=True)
    order_id: Mapped[str | None] = mapped_column(String, nullable=True)
    count_id: Mapped[str | None] = mapped_column(String, nullable=True)
    cause: Mapped[str | None] = mapped_column(String(30), nullable=True)
    proof_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    business_day: Mapped[date] = business_day_column()


class IngredientCount(Base):
    """A stock take (opname) of a branch's ingredients over a period."""

    __tablename__ = "ingredient_counts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    outlet_id: Mapped[str] = mapped_column(String)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(Text, default="web", server_default=text("'web'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class IngredientCountLine(Base):
    __tablename__ = "ingredient_count_lines"

    # Kolom id di database tanpa nilai bawaan (dulu diisi backend lama), jadi id dibuat di sini.
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    count_id: Mapped[str] = mapped_column(String)
    ingredient_id: Mapped[str | None] = mapped_column(String, nullable=True)
    ingredient_name: Mapped[str] = mapped_column(String(255))
    unit_id: Mapped[str | None] = mapped_column(String, nullable=True)
    book_balance: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    counted: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    value: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    shrink_tolerance: Mapped[Decimal] = mapped_column(Numeric(5, 2))


class IngredientCountDraft(Base):
    """A counted figure typed for a branch's next count and not closed yet; shared by every screen counting that branch."""

    __tablename__ = "ingredient_count_drafts"

    outlet_id: Mapped[str] = mapped_column(Text, primary_key=True)
    ingredient_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    counted: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


REQUEST_PENDING = "pending"
REQUEST_REJECTED = "rejected"
REQUEST_CLOSED = "closed"


class IngredientCountRequest(Base):
    """Pengajuan tutup periode dari tablet cabang; admin menutup periodenya di web atau menolaknya."""

    __tablename__ = "ingredient_count_requests"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    outlet_id: Mapped[str] = mapped_column(Text)
    period_start: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(Text, default=REQUEST_PENDING)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    count_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    # Pertama kali dibuka admin pemegang stok.opname; pengaju melihatnya sebagai tanda pengajuan sedang ditinjau.
    seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    seen_by: Mapped[str | None] = mapped_column(Text, nullable=True)


class IngredientCountChange(Base):
    """Who changed a counted figure of a closed count, from what to what; it outlives the count it came from."""

    __tablename__ = "ingredient_count_changes"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    outlet_id: Mapped[str] = mapped_column(Text)
    count_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingredient_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    ingredient_name: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    old_counted: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    new_counted: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RecipeIngredient(Base):
    """How much of an ingredient one portion of a menu item uses at a branch."""

    __tablename__ = "recipe_ingredients"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    outlet_id: Mapped[str] = mapped_column(String)
    menu_item_id: Mapped[str] = mapped_column(String)
    ingredient_id: Mapped[str] = mapped_column(String)
    catalog_id: Mapped[str | None] = mapped_column(String, nullable=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    # Kolom ini NOT NULL tanpa nilai bawaan di database, jadi setiap penulisan harus mengisinya.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
