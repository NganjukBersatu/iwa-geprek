"""HTTP surface of sign-in and sign-out; the tablet takes its token in the answer, a browser gets it as a cookie its scripts cannot read."""
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.attempts import refusal
from app.auth.mappers import session_out, user_out, token_out
from app.auth.schemas import AuthUserOut, BrowserSessionOut, LoginIn, TokenOut
from app.core.auth import CHANNEL_BEARER, CHANNEL_COOKIE, clear_session_cookie, current_user, end_session, session_cookie
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.http import public_base_url
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["v2-auth"])


def _device(request: Request) -> str | None:
    return request.headers.get("user-agent")


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    try:
        user, token, lifetime = service.login(db, body.username, body.password, CHANNEL_BEARER, _device(request))
    except DomainError as error:
        raise refusal(error) from error
    return token_out(user, token, lifetime, public_base_url())


@router.post("/session", response_model=BrowserSessionOut)
def browser_login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        user, token, lifetime = service.login(db, body.username, body.password, CHANNEL_COOKIE, _device(request))
    except DomainError as error:
        raise refusal(error) from error
    session_cookie(response, token, lifetime)
    return session_out(user, lifetime, public_base_url())


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: Session = Depends(get_db), _: User = Depends(current_user)):
    """Ends only the sign-in that sent this request; the person's other devices stay signed in."""
    end_session(db, request.state.login_session_id)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_session_cookie(response)
    # Only cookies: the page keeps what the person chose (branch, rows per page) for the next sign-in.
    response.headers["Clear-Site-Data"] = '"cookies"'
    return response


@router.get("/me", response_model=AuthUserOut)
def me(user: User = Depends(current_user)):
    return user_out(user, public_base_url())
