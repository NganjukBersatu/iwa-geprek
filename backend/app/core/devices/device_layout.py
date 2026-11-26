"""Tampilan app di satu perangkat: otomatis dari ukuran layar, atau dipaksa HP atau Tablet dari web admin."""
from typing import Literal

from starlette.requests import Request

DeviceLayout = Literal["auto", "phone", "tablet"]

AUTO: DeviceLayout = "auto"
# Hanya dua nilai yang disimpan; otomatis disimpan kosong (sama dengan CHECK check_devices_layout_values).
STORED = ("phone", "tablet")
# Nama kunci di request.state yang dibaca DeviceLayoutMarker.
STATE_KEY = "device_layout"


def shown(stored: str | None) -> DeviceLayout:
    if stored == "phone":
        return "phone"
    if stored == "tablet":
        return "tablet"
    return AUTO


def stored(layout: DeviceLayout) -> str | None:
    return None if layout == AUTO else layout


def mark(request: Request, stored_layout: str | None) -> None:
    """Satu pintu untuk semua jalur autentikasi perangkat: nilai ini disalin DeviceLayoutMarker menjadi header X-Device-Layout."""
    setattr(request.state, STATE_KEY, shown(stored_layout))
