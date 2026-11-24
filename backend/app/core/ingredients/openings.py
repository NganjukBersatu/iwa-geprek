"""Stok awal tiap bahan untuk periode opname yang sedang berjalan: satu pintu untuk tablet dan web.

Stok awal adalah stok tepat sebelum hari pertama periode. Selisihnya dengan saldo saat itu ditulis sebagai satu kartu penyesuaian
bertanda OPENING_CAUSE, dicap sedetik sebelum periode dimulai, sehingga kolom stok awal di laporan periode sama dengan angka yang diisi.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core import stock_balances
from app.core.ingredients import counts as ingredient_counts
from app.core.clock import today
from app.core.date_range import range_start
from app.core.ingredients.ledger import own_ingredient
from app.core.money import decimal_of
from app.models.ingredient import (
    INGREDIENT_ADJUSTMENT,
    INGREDIENT_IN,
    INGREDIENT_OUT,
    INGREDIENT_RND,
    INGREDIENT_WASTE,
    OPENING_CAUSE,
    OPENING_NOTE_PREFIX,
    Ingredient,
    IngredientCard,
)
from app.models.user import User

OPENING_LABEL = OPENING_NOTE_PREFIX + "{day:%d/%m/%Y}"


@dataclass(frozen=True)
class Opening:
    qty: Decimal
    user_id: str | None
    written_at: datetime


@dataclass(frozen=True)
class Journey:
    """Perjalanan stok satu bahan di periode berjalan, dari stok awal sampai stok sekarang."""

    start: date
    opening: Decimal
    opening_set: bool
    received: Decimal
    sold: Decimal
    wasted: Decimal
    trial: Decimal
    adjusted: Decimal
    stock: Decimal


def running_start(db: Session, outlet_id: str) -> date:
    """Hari pertama periode berjalan; bila periode sudah ditutup sampai hari ini, periode berikutnya mulai besok."""
    return ingredient_counts.running_starts(db, [outlet_id]).get(outlet_id) or today() + timedelta(days=1)


def boundary(start: date) -> datetime:
    return range_start(start) - timedelta(seconds=1)


def is_opening(start: date):
    """Kartu stok awal periode itu; kartu lama dari web belum bertanda sebab, jadi dikenali dari labelnya yang dibuat sistem."""
    return and_(
        IngredientCard.kind == INGREDIENT_ADJUSTMENT,
        IngredientCard.count_id.is_(None),
        IngredientCard.created_at == boundary(start),
        or_(IngredientCard.cause == OPENING_CAUSE, IngredientCard.note == OPENING_LABEL.format(day=start)),
    )


def is_opening_card(card: IngredientCard) -> bool:
    """Versi baris dari is_opening untuk kartu yang sudah dibaca; kartu lama dari web dikenali dari awalan labelnya."""
    if card.kind != INGREDIENT_ADJUSTMENT or card.count_id is not None:
        return False
    return card.cause == OPENING_CAUSE or (card.note or "").startswith(OPENING_LABEL.split("{")[0])


def openings(db: Session, outlet_id: str, start: date, ingredient_ids: list[str]) -> dict[str, Opening]:
    """Stok awal yang sudah diisi untuk bahan-bahan ini; bahan yang belum diisi tidak ada di hasilnya."""
    if not ingredient_ids:
        return {}
    rows = db.execute(
        select(IngredientCard.ingredient_id, IngredientCard.user_id, IngredientCard.created_at)
        .where(IngredientCard.outlet_id == outlet_id, IngredientCard.ingredient_id.in_(ingredient_ids), is_opening(start))
        .order_by(IngredientCard.ingredient_id, IngredientCard.id)
    ).all()
    found = {row[0]: row for row in rows}
    if not found:
        return {}
    befores = stock_balances.balances_before(db, outlet_id, start)
    return {ingredient_id: Opening(befores.get(ingredient_id, Decimal(0)), row[1], row[2]) for ingredient_id, row in found.items()}


def has_opening(start: date, ingredient_id):
    """Penyaring daftar: bahan yang stok awal periodenya sudah diisi."""
    return select(IngredientCard.id).where(IngredientCard.ingredient_id == ingredient_id, is_opening(start)).exists()


@dataclass(frozen=True)
class FillStatus:
    start: date
    total: int
    # Bahan aktif yang stok awal periode berjalannya belum diisi, urut nama.
    missing_ids: list[str]

    @property
    def filled(self) -> int:
        return self.total - len(self.missing_ids)


def fill_status(db: Session, outlet_id: str, start: date | None = None) -> FillStatus:
    """Stok awal satu periode (bawaan periode berjalan): berapa bahan aktif dan mana yang belum diisi; satu aturan untuk tablet dan web."""
    start = start or running_start(db, outlet_id)
    active = [Ingredient.outlet_id == outlet_id, Ingredient.is_active.is_(True)]
    total = db.scalar(select(func.count()).select_from(Ingredient).where(*active)) or 0
    missing = list(db.scalars(select(Ingredient.id).where(*active, ~has_opening(start, Ingredient.id)).order_by(Ingredient.name, Ingredient.id)).all())
    return FillStatus(start=start, total=total, missing_ids=missing)


def missing_counts(db: Session, outlet_ids: list[str]) -> dict[str, tuple[date, int]]:
    """Per cabang, hari pertama periode berjalan dan jumlah bahan aktif yang stok awalnya belum diisi; satu query per tanggal mulai yang berbeda."""
    starts = ingredient_counts.running_starts(db, outlet_ids)
    by_start: dict[date, list[str]] = {}
    for outlet_id, start in starts.items():
        by_start.setdefault(start, []).append(outlet_id)
    result: dict[str, tuple[date, int]] = {}
    for start, ids in by_start.items():
        rows = db.execute(
            select(Ingredient.outlet_id, func.count())
            .where(Ingredient.outlet_id.in_(ids), Ingredient.is_active.is_(True), ~has_opening(start, Ingredient.id))
            .group_by(Ingredient.outlet_id)
        ).all()
        for outlet_id, count in rows:
            result[outlet_id] = (start, count)
    return result


def write(db: Session, user: User, outlet_id: str, ingredient_id: str, value: Decimal, start: date) -> IngredientCard:
    """Menyamakan stok awal periode dengan angka yang diisi; kartu stok awal yang sudah ada diubah, bukan ditumpuk.

    Kartu stok awal adalah penanda bahan itu sudah diisi, jadi tetap dibuat atau dipertahankan walau selisihnya 0: bahan yang memang kosong tetap bisa ditandai terisi."""
    ingredient = own_ingredient(db, outlet_id, ingredient_id)
    stock_balances.hold(db, [ingredient.id], [])
    difference = value - stock_balances.balance_before(db, ingredient.id, start)
    existing = db.scalars(select(IngredientCard).where(IngredientCard.ingredient_id == ingredient.id, is_opening(start)).order_by(IngredientCard.id).with_for_update()).all()
    if existing:
        card = existing[0]
        if difference == 0:
            return card
        card.qty = decimal_of(card.qty) + difference
        card.cause = OPENING_CAUSE
        card.user_id = user.id
        db.commit()
        return card
    card = IngredientCard(
        outlet_id=outlet_id,
        ingredient_id=ingredient.id,
        ingredient_name=ingredient.name,
        kind=INGREDIENT_ADJUSTMENT,
        qty=difference,
        cause=OPENING_CAUSE,
        user_id=user.id,
        note=OPENING_LABEL.format(day=start),
        created_at=boundary(start),
    )
    db.add(card)
    db.commit()
    return card


def remove(db: Session, outlet_id: str, ingredient_id: str, start: date) -> None:
    """Menghapus stok awal periode; stok sekarang ikut berkurang sebesar itu."""
    ingredient = own_ingredient(db, outlet_id, ingredient_id)
    stock_balances.hold(db, [ingredient.id], [])
    for card in db.scalars(select(IngredientCard).where(IngredientCard.ingredient_id == ingredient.id, is_opening(start))).all():
        db.delete(card)
    db.commit()


def journey(db: Session, outlet_id: str, ingredient_id: str, start: date) -> Journey:
    ingredient = own_ingredient(db, outlet_id, ingredient_id)
    sums = dict(
        db.execute(
            select(IngredientCard.kind, func.coalesce(func.sum(IngredientCard.qty), 0))
            .where(IngredientCard.ingredient_id == ingredient.id, IngredientCard.business_day >= start)
            .group_by(IngredientCard.kind)
        ).all()
    )
    part = lambda kind: decimal_of(sums.get(kind, 0))  # noqa: E731
    opening_set = db.scalar(select(has_opening(start, ingredient.id))) or False
    return Journey(
        start=start,
        opening=stock_balances.balance_before(db, ingredient.id, start),
        opening_set=bool(opening_set),
        received=part(INGREDIENT_IN),
        sold=part(INGREDIENT_OUT),
        wasted=part(INGREDIENT_WASTE),
        trial=part(INGREDIENT_RND),
        adjusted=part(INGREDIENT_ADJUSTMENT),
        stock=decimal_of(ingredient.balance),
    )
