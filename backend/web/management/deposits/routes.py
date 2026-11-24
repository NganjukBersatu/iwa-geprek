"""HTTP surface of the deposits; every rule lives in the service. A deposit belongs to one branch: the readings may cover every branch, a write always names one."""
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache, uploads
from app.core.auth import current_user, readable_outlet_id, require_permission, writable_outlet_id
from app.core.branches import outlet_name, outlet_names
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.core.sorting import Sort
from app.core.finance import deposited
from app.core.finance.deposited import DayStateOut, DayStatesIn
from app.core.http import public_base_url
from app.models.user import User
from web.management.deposits import repository, service
from web.management.deposits.constants import PERMISSION_MANAGE, PERMISSION_VIEW
from web.management.deposits.mappers import DAY_SORTING, deposit_out
from web.management.deposits.schemas import DepositDayStateOut, DepositDaysOut, DepositIn, DepositNoteIn, DepositOut, DepositSummaryOut
from web.management.deposits.upload import RULE
from web.management.reports.common import month_to_date

router = APIRouter(prefix="/deposits", tags=["web-deposits"])

DAYS = TypeAdapter(DepositDaysOut)
DEPOSITS = TypeAdapter(list[DepositOut])


@contextmanager
def _domain_errors() -> Iterator[None]:
    """A business rule that rejects the request becomes the HTTP answer the screen reads."""
    try:
        yield
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error


def _one(db: Session, deposit_id: str) -> DepositOut:
    found = repository.with_user(db, deposit_id)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return deposit_out(found[0], found[1], public_base_url(), outlet_name(db, found[0].outlet_id) or "")


@router.get("/days", response_model=DepositDaysOut)
def days(
    start: Day | None = None,
    end: Day | None = None,
    sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    """The cash each day owes the owner, how much of it is settled, and the totals that say what is still held."""
    def build() -> DepositDaysOut:
        with _domain_errors():
            first, last, items, summary = service.days_view(db, outlet_id, start, end)
        rows = [DepositDayStateOut(day=item.day, due=item.due, paid=item.paid, left=item.left, status=item.status) for item in items]
        return DepositDaysOut(
            start=first,
            end=last,
            items=rows,
            open=DAY_SORTING.apply([row for row in rows if row.left > 0], sort),
            summary=DepositSummaryOut(**summary.__dict__),
        )

    return cache.read("web.deposits.days", (start, end, outlet_id, sort), build, DAYS, cache.REPORT_SECONDS)


# Not cached: it is read right before changing money, so it must be what the database holds now.
@router.post("/day-states", response_model=list[DayStateOut])
def day_states(
    body: DayStatesIn,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """What a change to money on these days would touch: handed over already, or a session still running."""
    return deposited.day_states(db, body, outlet_id, user.id)


@router.get("", response_model=list[DepositOut])
def list_deposits(
    start: Day | None = None,
    end: Day | None = None,
    share_sort: Sort = None,
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_VIEW)),
):
    with _domain_errors():
        first, last = month_to_date(start, end)
    base_url = public_base_url()

    def build() -> list[DepositOut]:
        found = repository.touching(db, outlet_id, service.plain(first), service.plain(last))
        names = outlet_names(db, [deposit.outlet_id for deposit, _ in found])
        return [deposit_out(deposit, name, base_url, names.get(deposit.outlet_id, ""), share_sort) for deposit, name in found]

    return cache.read("web.deposits", (first, last, outlet_id, base_url, share_sort), build, DEPOSITS, cache.REPORT_SECONDS)


@router.post("", response_model=DepositOut, status_code=status.HTTP_201_CREATED)
def create_deposit(
    body: DepositIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        deposit = service.create(db, user, outlet_id, service.DepositDraft(body.deposit_date, body.amount, body.note, body.days))
    return _one(db, deposit.id)


@router.patch("/{deposit_id}", response_model=DepositOut)
def update_note(
    deposit_id: str,
    body: DepositNoteIn,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.set_note(db, outlet_id, deposit_id, body.note)
    return _one(db, deposit_id)


@router.delete("/{deposit_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_deposit(
    deposit_id: str,
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        service.delete(db, outlet_id, deposit_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{deposit_id}/photo", response_model=DepositOut)
async def replace_photo(
    deposit_id: str,
    file: UploadFile = File(...),
    outlet_id: str = Depends(writable_outlet_id),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERMISSION_MANAGE)),
):
    with _domain_errors():
        image = await uploads.receive(file, RULE)
        service.set_photo(db, outlet_id, deposit_id, image, RULE)
    return _one(db, deposit_id)
