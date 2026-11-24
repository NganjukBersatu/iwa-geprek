from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SopSlide(Base):
    __tablename__ = "sop_slide"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    sop_id: Mapped[str] = mapped_column(String)
    sort_order: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(String)


class Sop(Base):
    __tablename__ = "sop"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean)
    sort_order: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer)
    # Empty means every branch.
    outlet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_by_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Saving replaces the slides whole, so a slide left out of the new list is deleted.
    slides: Mapped[list[SopSlide]] = relationship(
        SopSlide,
        primaryjoin="foreign(SopSlide.sop_id) == Sop.id",
        order_by="SopSlide.sort_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class SopRead(Base):
    __tablename__ = "sop_reads"

    sop_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text, primary_key=True)
    # Versi tertinggi yang dibaca sampai slide terakhir; lebih kecil dari Sop.version berarti belum membaca isi terbaru.
    version: Mapped[int] = mapped_column(Integer)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SopDraft(Base):
    """What one person is still writing; employees never see it, and saving the procedure removes it."""

    __tablename__ = "sop_drafts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String)
    sop_id: Mapped[str | None] = mapped_column(String, nullable=True)
    base_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
