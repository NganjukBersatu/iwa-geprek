"""HTTP surface of devices: a tablet pairs with its code, shows a QR and hears the scan, and the signed-in employee scans it."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import attempts
from app.core import live
from app.core.auth import current_device, current_user
from app.core.database import get_db
from app.core.devices import pairing
from app.core.errors import DomainError
from app.employee.devices import service
from app.employee.devices.constants import QR_LIFETIME_SECONDS
from app.employee.devices.schemas import LinkedDeviceOut, LinkIn, PairedDeviceOut, PairIn, QrOut
from app.models.device import Device
from app.models.user import User

router = APIRouter(prefix="/devices", tags=["v2-devices"])


@router.post("/pair", response_model=PairedDeviceOut)
def pair(body: PairIn, db: Session = Depends(get_db)):
    """Public, since the tablet has no token yet; the code itself is the proof, it stays valid until a new code is issued, and too many wrong codes lock pairing for a while."""
    hardware = pairing.Hardware(android_id=body.android_id, serial=body.serial, brand=body.brand, model=body.model)
    try:
        attempts.ensure_not_locked(db, attempts.PAIRING, attempts.PAIRING_SUBJECT)
        try:
            device, token = pairing.redeem(db, body.code, hardware)
        except DomainError:
            attempts.record_failure(db, attempts.PAIRING, attempts.PAIRING_SUBJECT)
            raise
    except DomainError as error:
        raise attempts.refusal(error) from error
    return PairedDeviceOut(id=device.id, outlet_id=device.outlet_id, name=device.name, section=device.section, token=token)


@router.post("/link", response_model=LinkedDeviceOut)
def link_device(body: LinkIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    try:
        device = service.link(db, user, body.token)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return LinkedDeviceOut(device_name=device.name, section=device.section)


@router.post("/qr", response_model=QrOut, status_code=201)
def issue_qr(db: Session = Depends(get_db), device: Device = Depends(current_device)):
    link_row, token = service.issue_qr(db, device)
    return QrOut(id=link_row.id, token=token, valid_seconds=QR_LIFETIME_SECONDS)


@router.get("/qr/{link_id}/stream")
async def qr_stream(link_id: str, db: Session = Depends(get_db), device: Device = Depends(current_device)):
    """The tablet waits here instead of asking: one status when the QR is scanned or runs out, then the stream ends."""
    try:
        service.ensure_own_qr(db, device.id, link_id)
    except DomainError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    device_id = device.id
    db.close()
    return live.stream_response(service.watch_qr(device_id, link_id))
