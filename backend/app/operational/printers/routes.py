from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.auth import current_user
from app.core.database import get_db
from app.core.devices import device_printers, print_routing, printer_categories
from app.core.devices.printer_category_schemas import PlanStationOut, PrinterCategoriesIn, PrinterReportIn, PrinterSetupOut, PrintPlanOut, setup_out
from app.core.errors import DomainError
from app.models.device import Device
from app.models.outlet import Outlet
from app.models.printer_category import PrinterSlot
from app.models.user import User
from app.operational.device import tablet

router = APIRouter(tags=["v2-operational-printers"])

# Tidak di-cache: daftar kecil milik cabang tablet dan harus langsung benar setelah diubah dari tablet atau web.


def _setup(db: Session, device: Device) -> PrinterSetupOut:
    return setup_out(printer_categories.setup_of(db, device.outlet_id), db.get_one(Outlet, device.outlet_id))


@router.get("/printer-categories", response_model=PrinterSetupOut)
def read(device: Device = Depends(tablet), db: Session = Depends(get_db)):
    return _setup(db, device)


@router.post("/printer-categories", response_model=PrinterSetupOut)
def add(body: PrinterCategoriesIn, device: Device = Depends(tablet), db: Session = Depends(get_db), user: User = Depends(current_user)):
    try:
        printer_categories.add(db, device.outlet_id, body.printer_slot, body.category_ids, user.id)
    except DomainError as error:
        db.rollback()
        raise HTTPException(status_code=error.status, detail=error.message) from error
    db.commit()
    return _setup(db, device)


@router.delete("/printer-categories/{category_id}", response_model=PrinterSetupOut)
def remove(category_id: str, device: Device = Depends(tablet), db: Session = Depends(get_db)):
    try:
        printer_categories.remove(db, device.outlet_id, category_id)
    except DomainError as error:
        db.rollback()
        raise HTTPException(status_code=error.status, detail=error.message) from error
    db.commit()
    return _setup(db, device)


# Tablet mengirim keadaan lengkap printernya saat dipasang, diganti, dilepas, atau sambungannya berubah.
@router.put("/printer-report", status_code=status.HTTP_204_NO_CONTENT)
def report(body: PrinterReportIn, device: Device = Depends(tablet), db: Session = Depends(get_db)):
    try:
        changed = device_printers.report(db, device.id, body.reported())
    except DomainError as error:
        db.rollback()
        raise HTTPException(status_code=error.status, detail=error.message) from error
    if changed:
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Tidak di-cache: rencana cetak berubah begitu tablet, stasiun, atau kategori diubah, dan tablet memuat ulang lewat sinyal live.
@router.get("/print-plan", response_model=PrintPlanOut)
def print_plan(device: Device = Depends(tablet), db: Session = Depends(get_db)):
    plan = print_routing.plan_for(db, device)
    return PrintPlanOut(
        receipt=plan.receipt,
        stations=[PlanStationOut(station_id=entry.station_id, name=entry.name, held=entry.held, category_ids=entry.category_ids, kind=entry.kind) for entry in plan.stations],
        mode=plan.mode,
        legacy_bar_station_id=plan.legacy_slots.get(PrinterSlot.BAR),
        legacy_kitchen_station_id=plan.legacy_slots.get(PrinterSlot.KITCHEN),
    )
