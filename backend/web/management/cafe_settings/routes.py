"""HTTP surface of the cafe settings; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import require_permission, writable_outlet_id
from app.core.database import get_db
from app.core.errors import DomainError
from app.models.user import User
from web.management.cafe_settings import service
from web.management.cafe_settings.constants import PERMISSION_MANAGE
from web.management.cafe_settings.mappers import settings_out
from web.management.cafe_settings.schemas import CafeSettingsIn, CafeSettingsOut

router = APIRouter(prefix="/cafe-settings", tags=["v2-cafe-settings"])

SETTINGS = TypeAdapter(CafeSettingsOut)


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.get("", response_model=CafeSettingsOut)
def read_settings(
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    def build() -> CafeSettingsOut:
        with _domain_errors():
            return settings_out(outlet_id, service.read(db, outlet_id))

    return cache.read("web.cafe-settings", (outlet_id,), build, SETTINGS, cache.REFERENCE_SECONDS)


@router.put("", response_model=CafeSettingsOut)
def update_settings(
    body: CafeSettingsIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        return settings_out(outlet_id, service.update(db, outlet_id, body.model_dump(exclude_unset=True)))
