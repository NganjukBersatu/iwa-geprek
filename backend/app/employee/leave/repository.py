"""Database reads for leave requests."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.employee.leave.constants import MINE_LIMIT
from app.models.leave_request import LeaveRequest


def mine(db: Session, user_id: str) -> list[LeaveRequest]:
    return list(
        db.scalars(
            select(LeaveRequest)
            .where(LeaveRequest.user_id == user_id)
            .order_by(LeaveRequest.created_at.desc())
            .limit(MINE_LIMIT)
        ).all()
    )


def find_owned(db: Session, user_id: str, request_id: str) -> LeaveRequest | None:
    """A request that belongs to someone else is treated as missing, so its existence is not revealed."""
    request = db.get(LeaveRequest, request_id)
    return request if request is not None and request.user_id == user_id else None
