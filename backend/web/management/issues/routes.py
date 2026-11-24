"""HTTP surface of the Laporan Masalah page."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import current_user, readable_outlet_id
from app.core.database import get_db
from app.models.user import User
from web.management.issues import service
from web.management.issues.mappers import issues_out
from web.management.issues.schemas import IssuesOut

router = APIRouter(prefix="/issues", tags=["web-issues"])


@router.get("", response_model=IssuesOut)
def list_issues(
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Every issue the person may see, now.

    Never cached: almost every detector depends on the clock (a shift starting, a range ending, a day passing), which no table version
    can follow. Each kind is filtered by the permission of its source data, so the route itself needs only a signed-in account.
    """
    found, names = service.issues(db, user, outlet_id)
    return issues_out(found, names)
