"""Many rows in one request: each row goes through the same service call as the single action, and one failed row never stops the rest."""
import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import messages
from app.core.auth import require_permission
from app.core.database import get_db
from app.core.errors import DomainError
from app.models.user import User

log = logging.getLogger(__name__)

# Enough for the menu or user of one cafe while keeping one request short; every row is its own transaction.
MAX_ROWS = 500


class BulkCreateIn(BaseModel):
    items: list[dict[str, Any]] = Field(max_length=MAX_ROWS)


class BulkIdsIn(BaseModel):
    ids: list[str] = Field(max_length=MAX_ROWS)


class BulkUpdateIn(BaseModel):
    ids: list[str] = Field(max_length=MAX_ROWS)
    changes: dict[str, Any] = Field(description="Only the fields to change, the same body as the single PATCH")


class BulkRowOut(BaseModel):
    row: int = Field(description="1 is the first row")
    ok: bool
    id: str | None = None
    error: str | None = None


class BulkResultOut(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[BulkRowOut]


def validation_message(error: ValidationError) -> str:
    parts = []
    for detail in error.errors():
        location = ".".join(str(part) for part in detail.get("loc", ()) if part != "__root__")
        text = detail.get("msg", messages.BULK_FIELD_INVALID)
        parts.append(f"{location}: {text}" if location else str(text))
    return "; ".join(parts) or messages.BULK_DATA_INVALID


def run(
    db: Session,
    rows: list[Any],
    action: Callable[[Any], Any],
    schema: type[BaseModel] | None = None,
) -> BulkResultOut:
    """Runs `action` per row, validating a dict row with `schema` first; `action` commits on its own."""
    results: list[BulkRowOut] = []
    for index, row in enumerate(rows, start=1):
        try:
            value = schema.model_validate(row) if schema is not None else row
            done = action(value)
            results.append(BulkRowOut(row=index, ok=True, id=getattr(done, "id", None)))
        except ValidationError as error:
            db.rollback()
            results.append(BulkRowOut(row=index, ok=False, error=validation_message(error)))
        except DomainError as error:
            db.rollback()
            results.append(BulkRowOut(row=index, ok=False, error=error.message))
        except IntegrityError:
            db.rollback()
            results.append(BulkRowOut(row=index, ok=False, error=messages.BULK_DUPLICATE))
        except Exception as error:  # noqa: BLE001 - one bad row must not bring down the rest
            db.rollback()
            log.exception("Bulk row %s failed", index)
            results.append(BulkRowOut(row=index, ok=False, error=messages.BULK_FAILED.format(error=type(error).__name__)))
    succeeded = sum(1 for result in results if result.ok)
    return BulkResultOut(total=len(results), succeeded=succeeded, failed=len(results) - succeeded, results=results)


def _no_context() -> None:
    return None


def add_bulk_routes(
    router: APIRouter,
    permission: str,
    *,
    create_schema: type[BaseModel] | None = None,
    create: Callable[[Session, Any, User, Any], Any] | None = None,
    create_context: Callable[..., Any] | None = None,
    update_schema: type[BaseModel] | None = None,
    update: Callable[[Session, str, Any, User], Any] | None = None,
    delete: Callable[[Session, str, User], Any] | None = None,
) -> None:
    """Adds POST /bulk, /bulk-update and /bulk-delete to a module's router for the actions it passes; every module shares these three routes.

    `create_context` is a dependency resolved once per request, such as the branch new rows are written to, and handed to `create`.
    """
    guard = require_permission(permission)
    context = create_context or _no_context

    if create is not None and create_schema is not None:

        @router.post("/bulk", response_model=BulkResultOut)
        def bulk_create(
            body: BulkCreateIn,
            db: Session = Depends(get_db),
            user: User = Depends(guard),
            resolved: Any = Depends(context),
        ):
            return run(db, body.items, lambda row: create(db, row, user, resolved), create_schema)

    if update is not None and update_schema is not None:

        @router.post("/bulk-update", response_model=BulkResultOut)
        def bulk_update(body: BulkUpdateIn, db: Session = Depends(get_db), user: User = Depends(guard)):
            try:
                changes = update_schema.model_validate(body.changes)
            except ValidationError as error:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=validation_message(error)) from error
            if not changes.model_fields_set:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.BULK_NOTHING_CHANGED)
            return run(db, body.ids, lambda row_id: update(db, row_id, changes, user))

    if delete is not None:

        @router.post("/bulk-delete", response_model=BulkResultOut)
        def bulk_delete(body: BulkIdsIn, db: Session = Depends(get_db), user: User = Depends(guard)):
            return run(db, body.ids, lambda row_id: delete(db, row_id, user))
