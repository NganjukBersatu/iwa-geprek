"""Requests to cancel an order, asked from the tablet of the order's branch; the rules live in app.core.orders.cancellations and the decision is made on the web."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import current_user
from app.core.database import get_db
from app.core.errors import DomainError
from app.core.orders import cancellations
from app.models.device import Device
from app.models.user import User
from app.operational.device import tablet

router = APIRouter(prefix="/cancellations", tags=["v2-operational-cancellations"])


class CancellationIn(BaseModel):
    order_id: str
    reason: str | None = Field(None, max_length=cancellations.MAX_REASON_LENGTH)


class CancellationCreatedOut(BaseModel):
    id: str
    order_id: str


@router.post("", response_model=CancellationCreatedOut, status_code=status.HTTP_201_CREATED)
def ask(body: CancellationIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(current_user)):
    try:
        row = cancellations.request(db, user, device.outlet_id, body.order_id, body.reason)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return CancellationCreatedOut(id=row.id, order_id=row.order_id)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def withdraw(request_id: str, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(current_user)):
    try:
        cancellations.withdraw(db, user, device.outlet_id, request_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
