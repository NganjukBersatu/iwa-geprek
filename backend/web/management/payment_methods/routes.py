"""HTTP surface of the payment method screen; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache, uploads
from app.core.auth import readable_outlet_id, require_permission, writable_outlet_id
from app.core.branches import outlet_name, outlet_names
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.core.http import public_base_url
from app.models.user import User
from web.management.payment_methods import service
from web.management.payment_methods.constants import PERMISSION_MANAGE
from web.management.payment_methods.mappers import SORTING, payment_method_out
from web.management.payment_methods.schemas import PaymentMethodCreateIn, PaymentMethodOut, PaymentMethodUpdateIn
from web.management.payment_methods.upload import RULE

router = APIRouter(prefix="/payment-methods", tags=["web-payment-methods"])

METHODS = TypeAdapter(list[PaymentMethodOut])


@contextmanager
def _domain_errors() -> Iterator[None]:
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


@router.get("", response_model=list[PaymentMethodOut])
def list_methods(
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    base_url = public_base_url()

    def build() -> list[PaymentMethodOut]:
        with _domain_errors():
            methods, usage = service.list_methods(db, outlet_id)
        names = outlet_names(db, [method.outlet_id for method in methods])
        rows = [payment_method_out(method, usage.get((method.outlet_id, method.code), 0), base_url, names.get(method.outlet_id, "")) for method in methods]
        return SORTING.apply(rows, sort)

    return cache.read("web.payment-methods", (outlet_id, base_url, sort), build, METHODS, cache.REFERENCE_SECONDS)


@router.get("/{method_id}", response_model=PaymentMethodOut)
def get_method(
    method_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    # A page opened by its address is not limited to the branch picked in the filter; only a branch-bound account is.
    with _domain_errors():
        method = service.get(db, user.locked_outlet_id, method_id)
    return payment_method_out(method, service.usage_of(db, method.outlet_id, method), public_base_url(), outlet_name(db, method.outlet_id) or "")


@router.post("", response_model=PaymentMethodOut, status_code=status.HTTP_201_CREATED)
def create_method(
    body: PaymentMethodCreateIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        method = service.create(db, outlet_id, body.code, body.label, body.icon, body.needs_change)
    return payment_method_out(method, 0, public_base_url(), outlet_name(db, outlet_id) or "")


@router.patch("/{method_id}", response_model=PaymentMethodOut)
def update_method(
    method_id: str,
    body: PaymentMethodUpdateIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        method = service.update(db, outlet_id, method_id, body.model_dump(exclude_unset=True))
    return payment_method_out(method, service.usage_of(db, outlet_id, method), public_base_url(), outlet_name(db, outlet_id) or "")


@router.delete("/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_method(
    method_id: str,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.delete(db, outlet_id, method_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{method_id}/image", response_model=PaymentMethodOut)
async def replace_image(
    method_id: str,
    file: UploadFile = File(...),
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        image = await uploads.receive(file, RULE)
        method = service.set_image(db, outlet_id, method_id, image)
    return payment_method_out(method, service.usage_of(db, outlet_id, method), public_base_url(), outlet_name(db, outlet_id) or "")


@router.delete("/{method_id}/image", response_model=PaymentMethodOut)
def remove_image(
    method_id: str,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        method = service.remove_image(db, outlet_id, method_id)
    return payment_method_out(method, service.usage_of(db, outlet_id, method), public_base_url(), outlet_name(db, outlet_id) or "")
