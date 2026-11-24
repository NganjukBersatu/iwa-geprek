from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Surface(StrEnum):
    MANAGEMENT = "management"
    EMPLOYEE = "employee"
    OPERATIONAL = "operational"


class ReleaseRead(Base):
    __tablename__ = "release_reads"

    user_id: Mapped[str] = mapped_column(Text, primary_key=True)
    surface: Mapped[Surface] = mapped_column(Text, primary_key=True)
    version: Mapped[str] = mapped_column(Text)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
