"""Jenis pesanan dan label yang dibaca orang, supaya pencarian menemukan pesanan dari kata yang tampil di layar."""
from sqlalchemy import case
from sqlalchemy.sql.elements import ColumnElement

from app.models.order import Order

DINE_IN = "free_table"
TAKE_AWAY = "take_away"

LABELS: dict[str, str] = {DINE_IN: "Makan di tempat", TAKE_AWAY: "Dibawa pulang"}
UNKNOWN_LABEL = "Jenis tidak dikenal"


def label_of() -> ColumnElement[str]:
    return case(LABELS, value=Order.order_type, else_=UNKNOWN_LABEL)
