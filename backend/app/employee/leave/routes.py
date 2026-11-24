"""HTTP surface of leave requests; every rule lives in the service."""
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.auth import current_user
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.http import public_base_url
from app.employee.leave import repository, service
from app.employee.leave.upload import RULE
from app.employee.leave.constants import MAX_LINK_LENGTH, MAX_REASON_LENGTH
from app.employee.leave.domain import LeaveForm
from app.employee.leave.mappers import leave_out
from app.employee.leave.schemas import EmployeeLeaveRequestOut
from app.models.leave_request import LeaveType
from app.models.user import User

router = APIRouter(prefix="/leave/requests", tags=["v2-leave"])


def _as_http(error: DomainError) -> HTTPException:
    return HTTPException(status_code=error.status, detail=error.message)


@router.post("", response_model=EmployeeLeaveRequestOut, status_code=status.HTTP_201_CREATED)
async def submit_request(
    type: LeaveType = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
    reason: str = Form(..., max_length=MAX_REASON_LENGTH),
    link: str | None = Form(None, max_length=MAX_LINK_LENGTH),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    try:
        attachment = await uploads.receive(file, RULE, required=False)
        created = service.submit(db, user, LeaveForm(type, start_date, end_date, reason, link), attachment)
    except DomainError as error:
        raise _as_http(error) from error
    return leave_out(created, public_base_url())


@router.get("/mine", response_model=list[EmployeeLeaveRequestOut])
def my_requests(db: Session = Depends(get_db), user: User = Depends(current_user)):
    base_url = public_base_url()
    return [leave_out(item, base_url) for item in repository.mine(db, user.id)]


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_request(request_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    try:
        service.cancel(db, user, request_id)
    except DomainError as error:
        raise _as_http(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
