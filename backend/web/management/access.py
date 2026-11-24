"""Who may use the management web at all: holders of full access, and roles ticked with web.masuk; every route here passes this first."""
from fastapi import Depends, HTTPException, status

from app.core.auth import current_user, may_enter_web
from app.models.user import User

NO_WEB_ACCESS = "Akun ini tidak punya akses ke web."


def web_user(user: User = Depends(current_user)) -> User:
    if not may_enter_web(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=NO_WEB_ACCESS)
    return user
