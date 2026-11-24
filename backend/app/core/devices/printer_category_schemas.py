"""Bentuk permintaan dan jawaban kategori printer, sama untuk tablet dan web admin."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.core.devices import device_printers, printer_categories
from app.models.outlet import Outlet, PrintMode
from app.models.printer_category import DeviceSlot, PrinterConnection, PrinterSlot
from app.models.station import StationKind


class PrinterCategoryOut(BaseModel):
    category_id: str
    name: str


class PrinterSetupOut(BaseModel):
    outlet_id: str
    outlet_name: str
    # Mode Stasiun: struk pesanan dicetak tablet stasiun, jadi tablet kasir hanya mencetak struk pembayaran.
    print_mode: PrintMode
    bar: list[PrinterCategoryOut]
    kitchen: list[PrinterCategoryOut]
    available: list[PrinterCategoryOut]


class PrinterCategoriesIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    printer_slot: PrinterSlot
    category_ids: list[str] = Field(min_length=1, max_length=printer_categories.MAX_PER_REQUEST)


def _entries(items: list[printer_categories.SlotCategory]) -> list[PrinterCategoryOut]:
    return [PrinterCategoryOut(category_id=item.category_id, name=item.name) for item in items]


def setup_out(setup: printer_categories.PrinterSetup, outlet: Outlet) -> PrinterSetupOut:
    return PrinterSetupOut(
        outlet_id=outlet.id,
        outlet_name=outlet.name,
        print_mode=PrintMode(outlet.print_mode),
        bar=_entries(setup.slots[PrinterSlot.BAR]),
        kitchen=_entries(setup.slots[PrinterSlot.KITCHEN]),
        available=_entries(setup.available),
    )


class ReportedPrinterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    printer_slot: DeviceSlot
    # Wajib untuk slot station dari APK yang mencetak per stasiun; APK lama mengirim slot tanpa stasiun.
    station_id: str | None = Field(None, min_length=1, max_length=64)
    printer_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=device_printers.MAX_NAME_LENGTH)]
    printer_address: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=device_printers.MAX_ADDRESS_LENGTH)]
    connection: PrinterConnection


class PrinterReportIn(BaseModel):
    """Keadaan lengkap printer tablet saat ini; slot yang tidak dikirim berarti belum dipasang."""

    model_config = ConfigDict(extra="forbid")

    printers: list[ReportedPrinterIn] = Field(max_length=device_printers.MAX_REPORTED)

    @model_validator(mode="after")
    def _one_per_slot(self) -> "PrinterReportIn":
        if any(item.station_id is not None and item.printer_slot != DeviceSlot.STATION for item in self.printers):
            raise ValueError("Stasiun hanya boleh dikirim untuk slot station.")
        if len({(item.printer_slot, item.station_id) for item in self.printers}) != len(self.printers):
            raise ValueError("Setiap slot printer hanya boleh dilaporkan sekali.")
        return self

    def reported(self) -> list[device_printers.ReportedPrinter]:
        return [
            device_printers.ReportedPrinter(
                slot=item.printer_slot, name=item.printer_name, address=item.printer_address, connection=item.connection, station_id=item.station_id
            )
            for item in self.printers
        ]


class PlanStationOut(BaseModel):
    station_id: str
    name: str
    # Benar bila tablet ini memegang stasiunnya; salah bila hanya mengirim struk ke printer stasiun tanpa tablet.
    held: bool
    # Menu dari kategori ini dicetak ke printer stasiun ini.
    category_ids: list[str]
    # Jenis stasiun; pengantar (deliver) menerima satu struk antar berisi seluruh pesanan.
    kind: StationKind


class PrintPlanOut(BaseModel):
    """Yang dicetak tablet ini: struk pembayaran bila memegang Kasir, dan satu printer per stasiun pada daftar."""

    receipt: bool
    stations: list[PlanStationOut]
    # Mode tablet: cashier tanpa Papan Stasiun, station dengan Papan Stasiun.
    mode: Literal["cashier", "station"]
    # Stasiun tujuan slot Bar dan Dapur dari APK lama, untuk memindahkan printer yang tersimpan di tablet sekali saja; kosong bila tidak pasti.
    legacy_bar_station_id: str | None
    legacy_kitchen_station_id: str | None
