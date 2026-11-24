from datetime import date

from sqlalchemy import Date, FetchedValue
from sqlalchemy.orm import Mapped, mapped_column


def business_day_column() -> Mapped[date]:
    # Hanya ditulis trigger database dari migrasi c3e5a7b9d104 untuk setiap aplikasi, lalu dibaca ulang ORM setelah setiap tulis.
    return mapped_column(Date, server_default=FetchedValue(), server_onupdate=FetchedValue())
