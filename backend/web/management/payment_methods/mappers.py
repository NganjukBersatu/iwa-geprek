"""Turns payment methods into their response schema."""
from app.core.finance.payment_methods import missing_requirements
from app.core.http import static_url
from app.core.sorting import RowSorting
from app.models.payment_method import PaymentMethod
from web.management.payment_methods.schemas import PaymentMethodOut


SORTING: RowSorting[PaymentMethodOut] = RowSorting(
    keys={
        "label": lambda row: row.label,
        "outlet": lambda row: row.outlet_name,
        "missing": lambda row: len(row.missing),
        "needs_change": lambda row: row.needs_change,
        "fee": lambda row: row.fee_percent,
        "used": lambda row: row.used_by_orders,
    },
    identity=lambda row: row.id,
)


def payment_method_out(method: PaymentMethod, used_by_orders: int, base_url: str, outlet_name: str) -> PaymentMethodOut:
    return PaymentMethodOut(
        id=method.id,
        outlet_id=method.outlet_id,
        outlet_name=outlet_name,
        code=method.code,
        label=method.label,
        icon=method.icon,
        position=method.position,
        is_active=method.is_active,
        needs_change=method.needs_change,
        note=method.note or "",
        fee_percent=method.fee_percent,
        image_url=static_url(base_url, method.image_path),
        used_by_orders=used_by_orders,
        missing=missing_requirements(method),
    )
