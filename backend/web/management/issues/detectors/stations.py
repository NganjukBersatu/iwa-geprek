from sqlalchemy import exists, func, select

from app.models.cash_session import CashSession, CashSessionStatus
from app.models.order import Order
from app.models.station import StationTask
from web.management.issues.domain import Issue, IssueKind, IssueLevel, Scope


def orders_off_board(scope: Scope) -> list[Issue]:
    # Satu per cabang: pesanan tanpa tugas stasiun selesai saat dibayar, jadi yang masih terbuka tanpa tugas berarti tugasnya gagal dibuat.
    running = select(CashSession.id).where(CashSession.status == CashSessionStatus.OPEN, CashSession.outlet_id.in_(scope.outlet_ids))
    rows = scope.db.execute(
        select(Order.outlet_id, func.count())
        .where(
            Order.outlet_id.in_(scope.outlet_ids),
            Order.cash_session_id.in_(running),
            Order.voided_at.is_(None),
            Order.served_at.is_(None),
            ~exists().where(StationTask.order_id == Order.id),
        )
        .group_by(Order.outlet_id)
        .order_by(Order.outlet_id)
    ).all()
    return [Issue(IssueKind.ORDER_OFF_BOARD, IssueLevel.PROBLEM, outlet_id, None, "", count=count) for outlet_id, count in rows]
