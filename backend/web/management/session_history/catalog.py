"""What the order correction dialog may choose from: the menu, variants, extras, promos and payment methods of one branch."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.catalog import selling
from app.core.errors import DomainError
from app.core.orders import promo as promo_rules
from app.models.order import Order
from app.models.payment_method import PaymentMethod
from app.models.promo import Promo
from web.management.session_history.schemas import (
    CatalogChoiceOut,
    CatalogExtraOut,
    CatalogMenuOut,
    CatalogMethodOut,
    CatalogPromoOut,
    CatalogVariantGroupOut,
    OrderCatalogOut,
)

NOT_FOUND = 404
ORDER_NOT_FOUND = "Transaksi tidak ditemukan."


def of_order(db: Session, order_id: str, outlet_id: str | None) -> OrderCatalogOut:
    order = db.get(Order, order_id)
    # Another branch's order answers as missing, so its existence is not revealed.
    if order is None or (outlet_id and order.outlet_id != outlet_id):
        raise DomainError(ORDER_NOT_FOUND, status=NOT_FOUND)
    branch = order.outlet_id

    def menu_out(item: selling.SellableMenu) -> CatalogMenuOut:
        return CatalogMenuOut(
            id=item.menu.id,
            name=item.menu.name,
            price=item.price,
            variant_groups=[
                CatalogVariantGroupOut(id=group.id, name=group.name, required=group.required, choices=[CatalogChoiceOut(id=choice.id, name=choice.name) for choice in group.choices])
                for group in item.variant_groups
            ],
            extras=[CatalogExtraOut(id=extra.id, name=extra.name, price=extra.price) for extra in item.extras],
        )

    promos = [CatalogPromoOut(id=promo_id, name=name, status="active") for promo_id, name in db.execute(select(Promo.id, Promo.name).where(promo_rules.in_effect(order.business_day)).order_by(Promo.name)).all()]
    if order.promo_id and all(promo.id != order.promo_id for promo in promos):
        used = db.get(Promo, order.promo_id)
        promos.insert(0, CatalogPromoOut(id=order.promo_id, name=used.name if used else "", status="ended" if used else "deleted"))

    rows = db.scalars(select(PaymentMethod).where(PaymentMethod.outlet_id == branch, PaymentMethod.is_active.is_(True)).order_by(PaymentMethod.position)).all()
    methods = [CatalogMethodOut(code=method.code, label=method.label, needs_change=method.needs_change, status="active") for method in rows]
    if order.payment_method and all(method.code != order.payment_method for method in methods):
        # The order keeps its own method even after the branch switched it off or deleted it, so the dialog never shows it blank.
        used = db.scalars(select(PaymentMethod).where(PaymentMethod.outlet_id == branch, PaymentMethod.code == order.payment_method)).first()
        methods.insert(
            0,
            CatalogMethodOut(
                code=order.payment_method,
                label=order.payment_method_label or (used.label if used else order.payment_method),
                needs_change=used.needs_change if used else order.cash_received is not None,
                status="inactive",
            ),
        )
    return OrderCatalogOut(menus=[menu_out(item) for item in selling.menus_of(db, branch)], promos=promos, methods=methods)
