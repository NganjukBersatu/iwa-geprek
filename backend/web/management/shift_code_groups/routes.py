"""HTTP surface of the shift codes as groups; every rule lives in the service."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, Response, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import bulk, cache
from app.core.auth import require_permission
from app.core.database import get_db
from app.core.errors import DomainError, refusal
from app.core.sorting import Sort
from app.models.user import User
from web.management.shift_code_groups import service
from web.management.shift_code_groups.constants import PERMISSION_MANAGE
from web.management.shift_code_groups.domain import GroupChanges, GroupDraft
from web.management.shift_code_groups.mappers import code_group_out, sorted_groups
from web.management.shift_code_groups.schemas import CodeGroupCreateIn, CodeGroupOut, CodeGroupUpdateIn

router = APIRouter(prefix="/shift-code-groups", tags=["v2-shift-code-groups"])

GROUPS = TypeAdapter(list[CodeGroupOut])
CATEGORY_NAMES = TypeAdapter(list[str])

ROW_FIELDS = ("code", "start_clock", "end_clock", "overtime_start_clock", "overtime_end_clock", "color", "is_day_off", "sort_order")


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise refusal(error) from error


def _draft(body: CodeGroupCreateIn) -> GroupDraft:
    return GroupDraft(**{**body.model_dump(exclude={"outlet_ids"}), "outlet_ids": tuple(body.outlet_ids)})


def _changes(body: CodeGroupUpdateIn) -> GroupChanges:
    sent = body.model_dump(exclude_unset=True)
    return GroupChanges(
        values={field: sent[field] for field in ROW_FIELDS if field in sent},
        category=sent.get("category"),
        outlet_ids=tuple(sent["outlet_ids"]) if sent.get("outlet_ids") is not None else None,
        crosses_midnight=sent.get("crosses_midnight"),
    )


@router.get("", response_model=list[CodeGroupOut])
def list_groups(sort: Sort = None, db: Session = Depends(get_db), admin: User = Depends(require_permission(PERMISSION_MANAGE))):
    return cache.read(
        "web.shift-code-groups",
        (admin.locked_outlet_id, sort),
        lambda: sorted_groups([code_group_out(group) for group in service.list_groups(db, admin)], sort),
        GROUPS,
        cache.REFERENCE_SECONDS,
    )


@router.get("/categories", response_model=list[str])
def categories(db: Session = Depends(get_db), _: User = Depends(require_permission(PERMISSION_MANAGE))):
    """Names already in use, offered while typing a category."""
    return cache.read("web.shift-code-groups.categories", (), lambda: service.category_names(db), CATEGORY_NAMES, cache.REFERENCE_SECONDS)


@router.post("", response_model=CodeGroupOut, status_code=status.HTTP_201_CREATED)
def create_group(body: CodeGroupCreateIn, db: Session = Depends(get_db), admin: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        return code_group_out(service.create_group(db, admin, _draft(body)))


@router.get("/{key}", response_model=CodeGroupOut)
def get_group(key: str, db: Session = Depends(get_db), admin: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        return code_group_out(service.get_group(db, admin, key))


@router.patch("/{key}", response_model=CodeGroupOut)
def update_group(key: str, body: CodeGroupUpdateIn, db: Session = Depends(get_db), admin: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        return code_group_out(service.update_group(db, admin, key, _changes(body)))


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(key: str, db: Session = Depends(get_db), admin: User = Depends(require_permission(PERMISSION_MANAGE))):
    with _domain_errors():
        service.delete_group(db, admin, key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


bulk.add_bulk_routes(
    router,
    PERMISSION_MANAGE,
    create_schema=CodeGroupCreateIn,
    create=lambda db, body, admin, _context: code_group_out(service.create_group(db, admin, _draft(body))),
    update_schema=CodeGroupUpdateIn,
    update=lambda db, key, body, admin: code_group_out(service.update_group(db, admin, key, _changes(body))),
    delete=lambda db, key, admin: service.delete_group(db, admin, key),
)
