from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import require_permission
from app.core.database import get_db
from app.core.errors import DomainError
from app.models.user import User
from web.management.devices.constants import PERMISSION_MANAGE
from web.management.printers import service
from web.management.printers.schemas import MenuRouteOut, StationRoutesOut

router = APIRouter(prefix="/printers", tags=["v2-printers"])

# Tidak di-cache: keadaan tablet dan printer berubah dari tablet kapan saja dan diperbarui lewat sinyal live.

may_manage = require_permission(PERMISSION_MANAGE)
MAX_ID_LENGTH = 64


def _failed(error: DomainError) -> HTTPException:
    return HTTPException(status_code=error.status, detail=error.message)


@router.get("/{outlet_id}", response_model=StationRoutesOut)
def stations(outlet_id: str, db: Session = Depends(get_db), user: User = Depends(may_manage)):
    try:
        return service.stations(db, user, outlet_id)
    except DomainError as error:
        raise _failed(error) from error


@router.get("/{outlet_id}/menu-route", response_model=MenuRouteOut)
def menu_route(outlet_id: str, menu_id: str = Query(min_length=1, max_length=MAX_ID_LENGTH), db: Session = Depends(get_db), user: User = Depends(may_manage)):
    try:
        return service.menu_route(db, user, outlet_id, menu_id)
    except DomainError as error:
        raise _failed(error) from error
