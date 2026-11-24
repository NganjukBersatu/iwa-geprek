"""HTTP surface of the employee's own account; every rule lives in the service."""
from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core import uploads
from app.core.auth import current_user
from app.core.database import get_db
from app.core.errors import DomainError, refusal
from app.core.http import public_base_url
from app.employee.profile import service
from app.employee.profile.mappers import profile_out
from app.employee.profile.upload import RULE
from app.employee.profile.schemas import PasswordChangeIn, ProfileOut, ProfileUpdateIn
from app.models.user import User

router = APIRouter(prefix="/profile", tags=["v2-profile"])


def _as_http(error: DomainError) -> HTTPException:
    return refusal(error)


@router.get("", response_model=ProfileOut)
def read_profile(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return profile_out(service.get_profile(db, user), public_base_url())


@router.patch("", response_model=ProfileOut)
def update_profile(
    body: ProfileUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    changes = {field: getattr(body, field) for field in body.model_fields_set}
    try:
        return profile_out(service.update_profile(db, user, changes), public_base_url())
    except DomainError as error:
        raise _as_http(error) from error


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(body: PasswordChangeIn, request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    try:
        service.change_password(db, user, body.current_password, body.new_password, request.state.login_session_id)
    except DomainError as error:
        raise _as_http(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/photo", response_model=ProfileOut)
async def replace_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    try:
        image = await uploads.receive(file, RULE)
        return profile_out(service.set_photo(db, user, image), public_base_url())
    except DomainError as error:
        raise _as_http(error) from error


@router.delete("/photo", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(db: Session = Depends(get_db), user: User = Depends(current_user)):
    service.remove_photo(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
