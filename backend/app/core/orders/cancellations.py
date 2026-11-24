"""The one door for requests to cancel an order: asked from the tablet, decided by someone else, and approved through the same void engine.

Whether a request still waits is read from `decided_at` alone; the status label is written for the record and never compared in a query.
"""
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.clock import now
from app.core.errors import DomainError
from app.core.finance.session_totals import refresh_closed
from app.core.orders.void import PERMISSION_VOID_CLOSED, apply_void
from app.models.cancellation_request import CancellationRequest, CancellationStatus
from app.models.cash_session import CashSession, CashSessionStatus
from app.models.order import Order
from app.models.user import User

PERMISSION_VOID = "order.void"
PERMISSION_DECIDE = "order.void.setujui"
MAX_REASON_LENGTH = 500
MAX_NOTE_LENGTH = 500

BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
CONFLICT = 409

ORDER_NOT_FOUND = "Pesanan tidak ditemukan."
REQUEST_NOT_FOUND = "Pengajuan tidak ditemukan."
ORDER_VOIDED = "Pesanan ini sudah dibatalkan."
OTHER_CASHIER = "Pesanan ini dibuat kasir lain."
SESSION_CLOSED = "Sesi kasirnya sudah ditutup. Pengajuan pembatalan untuk sesi yang tutup butuh izin 'order.void_shift_tutup'."
ALREADY_PENDING = "Pesanan ini sudah punya pengajuan pembatalan yang menunggu."
ALREADY_DECIDED = "Pengajuan ini sudah diputuskan."
NOT_YOURS = "Hanya pengaju atau pemegang izin persetujuan yang boleh menarik pengajuan ini."
OWN_REQUEST = "Pengajuan pembatalan sendiri tidak dapat diputuskan sendiri."


@dataclass(frozen=True)
class PendingPage:
    requests: list[CancellationRequest]
    total: int


def waiting() -> ColumnElement[bool]:
    """The single meaning of "still waiting" for every query."""
    return CancellationRequest.decided_at.is_(None)


def has_pending(db: Session, order_id: str) -> bool:
    return db.scalar(select(func.count()).select_from(CancellationRequest).where(CancellationRequest.order_id == order_id, waiting())) > 0


def pending_of_orders(db: Session, order_ids: list[str]) -> dict[str, CancellationRequest]:
    """The waiting request of each order asked for, in one query; at most one waits per order."""
    if not order_ids:
        return {}
    rows = db.scalars(select(CancellationRequest).where(CancellationRequest.order_id.in_(order_ids), waiting())).all()
    return {row.order_id: row for row in rows}


def latest_of_orders(db: Session, order_ids: list[str]) -> dict[str, CancellationRequest]:
    """Pengajuan terbaru setiap pesanan yang diminta, dalam satu query lewat indeks order_id."""
    if not order_ids:
        return {}
    rows = db.scalars(
        select(CancellationRequest)
        .where(CancellationRequest.order_id.in_(order_ids))
        .distinct(CancellationRequest.order_id)
        .order_by(CancellationRequest.order_id, CancellationRequest.created_at.desc(), CancellationRequest.id.desc())
    ).all()
    return {row.order_id: row for row in rows}


def pending_page(db: Session, outlet_ids: list[str], page: int, size: int) -> PendingPage:
    """Oldest first, since the customer of the oldest has waited longest; two queries whatever the page."""
    if not outlet_ids:
        return PendingPage(requests=[], total=0)
    conditions = (CancellationRequest.outlet_id.in_(outlet_ids), waiting())
    total = db.scalar(select(func.count()).select_from(CancellationRequest).where(*conditions)) or 0
    rows = db.scalars(
        select(CancellationRequest).where(*conditions).order_by(CancellationRequest.created_at, CancellationRequest.id).offset((page - 1) * size).limit(size)
    ).all()
    return PendingPage(requests=list(rows), total=int(total))


def request(db: Session, user: User, outlet_id: str, order_id: str, reason: str | None) -> CancellationRequest:
    """The order row is locked while checking, so two tablets asking at once leave one request."""
    order = db.get(Order, order_id, with_for_update=True)
    if order is None or order.outlet_id != outlet_id:
        raise DomainError(ORDER_NOT_FOUND, status=NOT_FOUND)
    if order.voided_at is not None:
        raise DomainError(ORDER_VOIDED)
    if order.cashier_id != user.id and not user.allows(PERMISSION_VOID):
        raise DomainError(OTHER_CASHIER, status=FORBIDDEN)
    session = db.get(CashSession, order.cash_session_id) if order.cash_session_id else None
    if session is not None and session.status == CashSessionStatus.CLOSED and not user.allows(PERMISSION_VOID_CLOSED):
        raise DomainError(SESSION_CLOSED)
    if has_pending(db, order.id):
        raise DomainError(ALREADY_PENDING, status=CONFLICT)

    row = CancellationRequest(
        id=str(uuid.uuid4()),
        order_id=order.id,
        outlet_id=order.outlet_id,
        requested_by_id=user.id,
        reason=(reason or "").strip()[:MAX_REASON_LENGTH] or None,
        status=CancellationStatus.PENDING,
        created_at=now(),
    )
    db.add(row)
    db.commit()
    return row


def withdraw(db: Session, user: User, outlet_id: str | None, request_id: str) -> None:
    """A withdrawn request leaves no trace, as if it was never asked."""
    row = _waiting(db, outlet_id, request_id)
    if row.requested_by_id != user.id and not user.allows(PERMISSION_DECIDE):
        raise DomainError(NOT_YOURS, status=FORBIDDEN)
    db.delete(row)
    db.commit()


def decide(db: Session, user: User, outlet_id: str | None, request_id: str, approve: bool, note: str | None) -> CancellationRequest:
    """An approval voids the order with the reason of the request; a closed session's figures are worked out again."""
    row = _waiting(db, outlet_id, request_id)
    if row.requested_by_id == user.id:
        raise DomainError(OWN_REQUEST, status=FORBIDDEN)
    order = db.get(Order, row.order_id, with_for_update=True)
    if order is None:
        raise DomainError(ORDER_NOT_FOUND, status=NOT_FOUND)
    if approve and order.voided_at is not None:
        raise DomainError(ORDER_VOIDED)

    row.status = CancellationStatus.APPROVED if approve else CancellationStatus.REJECTED
    row.decided_by_id = user.id
    row.decided_at = now()
    row.manager_note = (note or "").strip()[:MAX_NOTE_LENGTH] or None
    if approve:
        apply_void(db, order, row.reason, user.id)
        session = db.get(CashSession, order.cash_session_id) if order.cash_session_id else None
        if session is not None:
            refresh_closed(db, session)
    db.commit()
    return row


def _waiting(db: Session, outlet_id: str | None, request_id: str) -> CancellationRequest:
    """Locked for the decision; `outlet_id` limits it to one branch, None to none."""
    row = db.get(CancellationRequest, request_id, with_for_update=True)
    if row is None or (outlet_id is not None and row.outlet_id != outlet_id):
        raise DomainError(REQUEST_NOT_FOUND, status=NOT_FOUND)
    if row.decided_at is not None:
        raise DomainError(ALREADY_DECIDED, status=CONFLICT)
    return row
