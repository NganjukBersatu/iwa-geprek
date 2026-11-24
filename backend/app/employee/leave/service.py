"""Submitting and cancelling a leave request, with its attachment, as one step."""
import uuid

from sqlalchemy.orm import Session

from app.core import uploads
from app.core.errors import DomainError
from app.core.uploads import UploadedFile
from app.employee.leave import messages, repository, rules
from app.employee.leave.upload import RULE
from app.employee.leave.constants import ATTACHMENT_FOLDER
from app.employee.leave.domain import LeaveForm
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.user import User


def submit(db: Session, user: User, form: LeaveForm, attachment: UploadedFile | None) -> LeaveRequest:
    """An attachment replaces the link, and a failed upload leaves no request behind."""
    rules.check_period(form.start_date, form.end_date)
    request = LeaveRequest(
        id=str(uuid.uuid4()),
        outlet_id=user.working_outlet_id,
        user_id=user.id,
        type=form.type,
        start_date=form.start_date,
        end_date=form.end_date,
        reason=rules.clean_reason(form.reason),
        status=LeaveStatus.PENDING,
        attachment_link=None if attachment else rules.clean_link(form.link),
    )
    db.add(request)
    if attachment is not None:
        path = f"{ATTACHMENT_FOLDER}/{request.id}{attachment.extension}"
        uploads.store(db, path, attachment, RULE)
        request.attachment_path = path
    db.commit()
    db.refresh(request)
    return request


def cancel(db: Session, user: User, request_id: str) -> None:
    request = repository.find_owned(db, user.id, request_id)
    if request is None:
        raise DomainError(messages.NOT_FOUND, status=404)
    if request.status != LeaveStatus.PENDING:
        raise DomainError(messages.ALREADY_DECIDED)
    path = request.attachment_path
    db.delete(request)
    db.commit()
    uploads.discard(db, path)
