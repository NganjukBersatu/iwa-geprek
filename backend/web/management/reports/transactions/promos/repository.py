"""Database reads of the promo report."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.promo import Promo


def order_count(db: Session, conditions: tuple) -> int:
    return int(db.scalar(select(func.count()).select_from(Order).where(*conditions)) or 0)


def discount_rows(db: Session, conditions: tuple) -> list[tuple]:
    return db.execute(
        select(
            Order.promo_id,
            func.count(),
            func.count().filter(Order.total <= 0),
            func.coalesce(func.sum(Order.discount), 0),
            func.coalesce(func.sum(Order.total), 0),
        )
        .where(*conditions, Order.discount > 0)
        .group_by(Order.promo_id)
        .order_by(func.sum(Order.discount).desc())
    ).all()


def promos_by_id(db: Session, promo_ids: list[str]) -> dict[str, Promo]:
    if not promo_ids:
        return {}
    return {promo.id: promo for promo in db.scalars(select(Promo).where(Promo.id.in_(promo_ids))).all()}
