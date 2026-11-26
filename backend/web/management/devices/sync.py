"""When a branch's device-facing data last changed, so the web can tell whether a device has been in touch since."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem, MenuOutletPrice
from app.models.payment_method import PaymentMethod
from app.models.promo import Promo


def data_changed_at(db: Session, outlet_ids: list[str]) -> dict[str, datetime | None]:
    """Latest change per branch over menu, branch prices, promos and payment methods; four small aggregate queries."""
    if not outlet_ids:
        return {}
    everywhere = [db.scalar(select(func.max(model.updated_at))) for model in (MenuItem, Promo)]
    prices = dict(
        db.execute(
            select(MenuOutletPrice.outlet_id, func.max(MenuOutletPrice.updated_at))
            .where(MenuOutletPrice.outlet_id.in_(outlet_ids))
            .group_by(MenuOutletPrice.outlet_id)
        ).all()
    )
    methods = dict(
        db.execute(
            select(PaymentMethod.outlet_id, func.max(PaymentMethod.updated_at))
            .where(PaymentMethod.outlet_id.in_(outlet_ids))
            .group_by(PaymentMethod.outlet_id)
        ).all()
    )
    latest: dict[str, datetime | None] = {}
    for outlet_id in outlet_ids:
        moments = [moment for moment in (*everywhere, prices.get(outlet_id), methods.get(outlet_id)) if moment is not None]
        latest[outlet_id] = max(moments) if moments else None
    return latest


def has_latest_data(last_used_at: datetime | None, changed: datetime | None) -> bool | None:
    """None while the device has never been used; otherwise whether it was in touch at or after the latest change."""
    if last_used_at is None:
        return None
    return changed is None or last_used_at >= changed
