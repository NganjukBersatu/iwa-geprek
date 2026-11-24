from app.models.cafe_settings import CafeSettings
from web.management.cafe_settings.schemas import CafeSettingsOut

_EMPTY = dict(name="", address="", phone="", complaint_number="", wifi=[], wifi_password="", social=[], receipt_greeting="", cost_markup_percent=0, target_margin_percent=None, tax_percent=0, service_percent=0)


def settings_out(outlet_id: str, row: CafeSettings | None) -> CafeSettingsOut:
    if row is None:
        return CafeSettingsOut(outlet_id=outlet_id, exists=False, **_EMPTY)
    return CafeSettingsOut(
        outlet_id=outlet_id,
        exists=True,
        name=row.name,
        address=row.address or "",
        phone=row.phone or "",
        complaint_number=row.complaint_number or "",
        wifi=[{"area": w.get("area", ""), "ssid": w.get("ssid", "")} for w in row.wifi or []],
        wifi_password=row.wifi_password or "",
        social=[{"icon": s.get("ikon", ""), "handle": s.get("handle", "")} for s in row.social or []],
        receipt_greeting=row.receipt_greeting or "",
        cost_markup_percent=row.cost_markup_percent,
        target_margin_percent=row.target_margin_percent,
        tax_percent=row.tax_percent,
        service_percent=row.service_percent,
    )
