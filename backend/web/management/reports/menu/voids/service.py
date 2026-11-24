"""Builds the voids report, ranged by when the orders were voided."""
from datetime import date

from sqlalchemy.orm import Session

from app.core.business_days import valid_orders_in
from app.core.money import ZERO, decimal_of
from web.management.reports.common import month_to_date, optional_percent, user_usernames
from web.management.reports.menu import item_summary, messages
from web.management.reports.menu.sold_orders import count_orders
from web.management.reports.menu.voids import repository
from web.management.reports.menu.voids.domain import VoidedOrder, Voids, VoidsByUser


def voids(db: Session, start: date | None, end: date | None, sort: str | None, page: int, per_page: int, outlet_id: str | None) -> Voids:
    """Count, value, and the per-voider tally cover every void in the range; only the list is paged."""
    start, end = month_to_date(start, end)
    conditions = repository.voided_between(start, end, outlet_id)
    count, total_value = repository.void_totals(db, conditions)
    count = int(count or 0)
    tallies = repository.voids_by_user(db, conditions)
    orders = repository.voided_page(db, conditions, sort, page, per_page)
    valid = count_orders(db, valid_orders_in(start, end, outlet_id))

    names = user_usernames(
        db,
        {order.cashier_id for order in orders}
        | {order.voided_by_id for order in orders if order.voided_by_id}
        | {voider for voider, _, _ in tallies if voider},
    )
    texts = item_summary.summaries(db, [order.id for order in orders])

    by_user: dict[str, list] = {}
    for voider, voided, total in tallies:
        username = (names.get(voider) if voider else None) or messages.UNRECORDED_USER
        tally = by_user.setdefault(username, [0, ZERO])
        tally[0] += int(voided)
        tally[1] += decimal_of(total)

    return Voids(
        start=start,
        end=end,
        count=count,
        total_value=decimal_of(total_value),
        valid_transactions=valid,
        void_percent=optional_percent(count, valid + count),
        by_user=sorted(
            (VoidsByUser(username=username, count=voided, total=total) for username, (voided, total) in by_user.items()),
            key=lambda tally: tally.count,
            reverse=True,
        ),
        orders=[
            VoidedOrder(
                order_id=order.id,
                created_at=order.created_at,
                voided_at=order.voided_at,
                customer_name=order.customer_name,
                table_no=order.table_no,
                total=decimal_of(order.total),
                reason=order.void_reason,
                cashier_username=names.get(order.cashier_id),
                voided_by=names.get(order.voided_by_id) if order.voided_by_id else None,
                items_summary=texts.get(order.id, ""),
            )
            for order in orders
        ],
        page=page,
        per_page=per_page,
    )
