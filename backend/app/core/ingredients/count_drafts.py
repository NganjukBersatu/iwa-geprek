"""Draf hitungan opname: jumlah real yang sudah diketik tetapi belum ditutup, satu draf per cabang yang dipakai web dan tablet bersama.

Draf tersimpan setiap kali orang mengetik, jadi layar yang tertutup atau tablet yang mati tidak menghilangkan hitungan; menutup periode menghapusnya.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.clock import now
from app.core.errors import DomainError
from app.core.ingredients import messages
from app.models.ingredient import Ingredient, IngredientCountDraft
from app.models.user import User

NOT_FOUND = 404


@dataclass(frozen=True)
class DraftLine:
    """Jumlah real satu bahan; kosong berarti isiannya dihapus dari draf."""

    ingredient_id: str
    counted: Decimal | None


@dataclass(frozen=True)
class DraftEntry:
    ingredient_id: str
    counted: Decimal
    user_name: str | None
    updated_at: datetime


def read(db: Session, outlet_id: str) -> list[DraftEntry]:
    rows = db.execute(
        select(IngredientCountDraft, func.coalesce(User.name, User.username))
        .outerjoin(User, User.id == IngredientCountDraft.user_id)
        .where(IngredientCountDraft.outlet_id == outlet_id)
        .order_by(IngredientCountDraft.ingredient_id)
    ).all()
    return [DraftEntry(draft.ingredient_id, draft.counted, name, draft.updated_at) for draft, name in rows]


def save(db: Session, user: User, outlet_id: str, lines: list[DraftLine]) -> None:
    """Menyimpan isian yang berubah dalam satu perintah: yang berisi ditulis, yang kosong dihapus; bahan cabang lain ditolak."""
    ids = [line.ingredient_id for line in lines]
    if len(set(ids)) != len(ids):
        raise DomainError(messages.DUPLICATE_LINE)
    own = set(db.scalars(select(Ingredient.id).where(Ingredient.id.in_(ids), Ingredient.outlet_id == outlet_id)))
    if len(own) != len(ids):
        raise DomainError(messages.INGREDIENTS_NOT_FOUND, status=NOT_FOUND)
    cleared = [line.ingredient_id for line in lines if line.counted is None]
    kept = [line for line in lines if line.counted is not None]
    if cleared:
        db.execute(delete(IngredientCountDraft).where(IngredientCountDraft.outlet_id == outlet_id, IngredientCountDraft.ingredient_id.in_(cleared)))
    if kept:
        stamp = now()
        statement = insert(IngredientCountDraft).values(
            [{"outlet_id": outlet_id, "ingredient_id": line.ingredient_id, "counted": line.counted, "user_id": user.id, "updated_at": stamp} for line in kept]
        )
        db.execute(
            statement.on_conflict_do_update(
                index_elements=[IngredientCountDraft.outlet_id, IngredientCountDraft.ingredient_id],
                set_={"counted": statement.excluded.counted, "user_id": statement.excluded.user_id, "updated_at": statement.excluded.updated_at},
            )
        )
    db.commit()


def discard(db: Session, outlet_id: str) -> None:
    """Dipanggil di dalam transaksi penutupan periode, yang meng-commit sendiri."""
    db.execute(delete(IngredientCountDraft).where(IngredientCountDraft.outlet_id == outlet_id))
