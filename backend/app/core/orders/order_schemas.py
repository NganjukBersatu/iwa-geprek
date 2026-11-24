"""The shape of an order read back with its lines; the session history screen and the tablet both send it."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.core.orders.reading import OrderLines
from app.core.sorting import RowSorting
from app.models.cancellation_request import CancellationRequest, CancellationStatus
from app.models.order_item import OrderItem
from app.models.order_item_option import EXTRA, VARIANT, OrderItemOption


class SessionOrderExtraOut(BaseModel):
    extra_id: str | None
    name: str
    qty: int
    price: Decimal


class SessionOrderItemOut(BaseModel):
    id: str
    menu_item_id: str | None
    name: str
    qty: int
    unit_price: Decimal
    subtotal: Decimal
    note: str | None
    variant_ids: list[str]
    variant_names: list[str]
    extras: list[SessionOrderExtraOut]


class SessionOrderOut(BaseModel):
    id: str
    outlet_id: str
    # Sesi kasir tempat pesanan ini tercatat; kosong untuk pesanan tanpa sesi.
    session_id: str | None = None
    business_day: date
    receipt_number: str | None
    created_at: datetime
    customer_name: str | None
    table_no: str | None
    order_type: str
    note: str | None
    payment_method: str | None
    payment_method_label: str | None
    cash_received: Decimal | None
    promo_id: str | None
    promo_name: str | None
    discount: Decimal
    partner_covered: Decimal
    total: Decimal
    voided: bool
    # An open bill is written and sent to the stations but not paid yet; a payer sends back the version it saw.
    is_open: bool = False
    version: int = 1
    items: list[SessionOrderItemOut]


CancellationState = Literal["pending", "approved", "rejected"]


class OrderCancellationOut(BaseModel):
    id: str
    status: CancellationState
    requested_by_id: str
    requested_by_name: str | None
    reason: str | None


class StationOrderOut(SessionOrderOut):
    cashier_name: str | None
    served: bool
    # Pengajuan pembatalan terbaru pesanan ini; kosong bila belum pernah diajukan.
    cancellation: OrderCancellationOut | None


class StationOrderPageOut(BaseModel):
    orders: list[StationOrderOut]
    # Kosong berarti halaman terakhir.
    next_cursor: str | None


SESSION_ORDER_SORTING: RowSorting[SessionOrderOut] = RowSorting(
    keys={
        "customer": lambda row: row.customer_name,
        "created_at": lambda row: row.created_at,
        "method": lambda row: row.payment_method_label,
        "total": lambda row: row.total,
    },
    identity=lambda row: row.id,
)


def order_out(lines: OrderLines) -> SessionOrderOut:
    order = lines.order
    return SessionOrderOut(
        id=order.id,
        outlet_id=order.outlet_id,
        session_id=order.cash_session_id,
        business_day=order.business_day,
        receipt_number=order.receipt_number,
        created_at=order.created_at,
        customer_name=order.customer_name,
        table_no=order.table_no,
        order_type=order.order_type,
        note=order.note_label,
        payment_method=order.payment_method,
        payment_method_label=order.payment_method_label,
        cash_received=order.cash_received,
        promo_id=order.promo_id,
        promo_name=lines.promo_name,
        discount=order.discount,
        partner_covered=order.partner_covered,
        total=order.total,
        voided=order.voided_at is not None,
        is_open=order.is_open,
        version=order.version,
        items=[_item_out(item, lines.options.get(item.id, [])) for item in lines.items],
    )


def _item_out(item: OrderItem, options: list[OrderItemOption]) -> SessionOrderItemOut:
    variants = [option for option in options if option.kind == VARIANT]
    return SessionOrderItemOut(
        id=item.id,
        menu_item_id=item.menu_item_id,
        name=item.menu_item_name,
        qty=item.qty,
        unit_price=item.unit_price,
        subtotal=item.subtotal,
        note=item.note,
        variant_ids=[option.ref_id for option in variants if option.ref_id],
        variant_names=[option.name for option in variants],
        extras=[SessionOrderExtraOut(extra_id=option.ref_id, name=option.name, qty=option.qty, price=option.price) for option in options if option.kind == EXTRA],
    )


def cancellation_state(request: CancellationRequest) -> CancellationState:
    # Menunggu dibaca dari diputus_pada saja; label status hanya membedakan hasil putusan.
    if request.decided_at is None:
        return "pending"
    return "approved" if request.status == CancellationStatus.APPROVED else "rejected"


def station_order_out(
    lines: OrderLines, names: dict[str, str], cancellation: CancellationRequest | None
) -> StationOrderOut:
    order = lines.order
    return StationOrderOut(
        **order_out(lines).model_dump(),
        cashier_name=names.get(order.cashier_id),
        served=order.served_at is not None,
        cancellation=None
        if cancellation is None
        else OrderCancellationOut(
            id=cancellation.id,
            status=cancellation_state(cancellation),
            requested_by_id=cancellation.requested_by_id,
            requested_by_name=names.get(cancellation.requested_by_id),
            reason=cancellation.reason,
        ),
    )
