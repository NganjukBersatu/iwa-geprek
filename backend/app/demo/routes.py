"""The demo switch: started from the management web's sign-in page, so reading and starting it need no account; leaving it needs full access."""
import logging

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.mappers import session_out
from app.auth.schemas import BrowserSessionOut
from app.core.auth import CHANNEL_COOKIE, clear_session_cookie, require_full_access, session_cookie, start_session
from app.core.database import get_db
from app.core.demo import switch
from app.core.errors import CONFLICT, NOT_FOUND, DomainError
from app.core.http import public_base_url
from app.demo import messages
from app.demo.schemas import DemoStatusOut
from app.models.user import User

log = logging.getLogger(__name__)
router = APIRouter(prefix="/demo", tags=["v2-demo"])


def _out(found: switch.Status) -> DemoStatusOut:
    return DemoStatusOut(available=found.available, active=found.active, stage=found.stage, percent=found.percent, error_code=found.error_code)


@router.get("", response_model=DemoStatusOut)
def read_status():
    return _out(switch.status())


@router.post("", response_model=DemoStatusOut, status_code=status.HTTP_202_ACCEPTED)
def start():
    """Starts preparing in the background and answers at once; the page asks GET /v2/demo until the stage is ready."""
    try:
        found = switch.start()
    except switch.DemoUnavailable as error:
        raise DomainError(messages.UNAVAILABLE, status=NOT_FOUND, code="DEMO_UNAVAILABLE") from error
    except switch.CashierStillOpen as error:
        raise DomainError(messages.CASHIER_OPEN, status=CONFLICT, code="DEMO_CASHIER_OPEN") from error
    log.info("demo start requested: stage=%s", found.stage)
    return _out(found)


@router.post("/session", response_model=BrowserSessionOut)
def enter(request: Request, response: Response, db: Session = Depends(get_db)):
    """Signs the browser in as the demo owner; the database already answers from the demo schema once the switch is on."""
    if not switch.status().active:
        raise DomainError(messages.NOT_READY, status=CONFLICT, code="DEMO_NOT_READY")
    owner_id = switch.demo_owner_id(db.connection())
    owner = db.get(User, owner_id) if owner_id else None
    if owner is None:
        raise DomainError(messages.NOT_READY, status=CONFLICT, code="DEMO_NOT_READY")
    token, lifetime = start_session(db, owner, CHANNEL_COOKIE, request.headers.get("user-agent"))
    session_cookie(response, token, lifetime)
    return session_out(owner, lifetime, public_base_url())


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def leave(user: User = Depends(require_full_access), db: Session = Depends(get_db)):
    """Removes every demo row at once; every app reads the real data again on its next request."""
    if not switch.status().active:
        raise DomainError(messages.NOT_ACTIVE, status=CONFLICT, code="DEMO_NOT_ACTIVE")
    user_id = user.id
    # Transaksi permintaan ini sendiri memegang kunci baca pada tabel demo (saat memeriksa akun); harus selesai sebelum skemanya dihapus.
    db.commit()
    db.close()
    log.info("demo stop requested by user=%s", user_id)
    try:
        switch.stop()
    except switch.DemoBusy as error:
        raise DomainError(messages.BUSY, status=CONFLICT, code="DEMO_BUSY") from error
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_session_cookie(response)
    response.headers["Clear-Site-Data"] = '"cookies"'
    return response
