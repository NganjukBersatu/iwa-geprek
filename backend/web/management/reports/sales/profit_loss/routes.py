"""HTTP surface of the profit and loss report, rebuilt from the legacy /laporan routes."""
from fastapi import APIRouter, Depends, Query
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core import cache
from app.core.auth import readable_outlet_id, require_gate
from app.core.database import get_db
from app.core.date_range import Day
from app.core.errors import DomainError
from app.models.user import User
from web.management.reports.common import as_http
from web.management.reports.sales.profit_loss import service
from web.management.reports.sales.profit_loss.mappers import profit_loss_out
from web.management.reports.sales.profit_loss.schemas import ProfitLossOut
from web.management.reports import gates

router = APIRouter(prefix="/reports/profit-loss", tags=["v2-reports"])

SHAPE = TypeAdapter(ProfitLossOut)


@router.get("", response_model=ProfitLossOut)
def profit_loss(
    start: Day | None = Query(None, description="Defaults to today"),
    end: Day | None = Query(None, description="Defaults to start"),
    outlet_id: str | None = Depends(readable_outlet_id),
    db: Session = Depends(get_db),
    user: User = Depends(require_gate(gates.PROFIT_LOSS)),
):
    """Revenue less cost of goods sold, other ingredient costs, and operating expenses."""
    try:
        return cache.read(
            "web.reports.profit-loss",
            (start, end, outlet_id),
            lambda: profit_loss_out(service.profit_loss(db, start, end, outlet_id)),
            SHAPE,
            cache.REPORT_SECONDS,
        )
    except DomainError as error:
        raise as_http(error) from error
