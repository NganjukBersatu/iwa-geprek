"""The serving stages of a branch; a new order starts at the one marked first."""
from sqlalchemy.orm import Session

from app.models.cafe_settings import CafeSettings

CODE = "kode"
FIRST = "awal"
LAST = "akhir"
DEFAULT_STAGES: tuple[dict, ...] = (
    {"kode": "pending", "label": "Menunggu", "warna": "amber", "awal": True, "akhir": False},
    {"kode": "selesai", "label": "Selesai", "warna": "green", "awal": False, "akhir": True},
)


def of_branch(db: Session, outlet_id: str) -> list[dict]:
    settings = db.get(CafeSettings, outlet_id)
    stages = settings.order_stages if settings is not None else None
    return list(stages) if stages else list(DEFAULT_STAGES)


def first_code(db: Session, outlet_id: str) -> str:
    stages = of_branch(db, outlet_id)
    return next((stage[CODE] for stage in stages if stage.get(FIRST)), stages[0][CODE])
