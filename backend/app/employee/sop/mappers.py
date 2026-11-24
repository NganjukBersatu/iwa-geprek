"""Turns procedures into response schemas."""
from app.core.http import public_base_url, with_current_sop_media
from app.employee.sop.schemas import SlideOut, SopOut, SopReadOut, SopSummaryOut
from app.models.sop import Sop, SopRead


def summary_out(sop: Sop, outlets: dict[str, str]) -> SopSummaryOut:
    return SopSummaryOut(
        id=sop.id,
        title=sop.title,
        version=sop.version,
        slide_count=len(sop.slides),
        updated_at=sop.updated_at,
        outlet_name=outlets.get(sop.outlet_id) if sop.outlet_id else None,
    )


def sop_out(sop: Sop, outlets: dict[str, str]) -> SopOut:
    base = public_base_url()
    return SopOut(
        **summary_out(sop, outlets).model_dump(),
        slides=[SlideOut(id=slide.id, title=slide.title, body=with_current_sop_media(slide.body, base)) for slide in sop.slides],
    )


def read_out(read: SopRead) -> SopReadOut:
    return SopReadOut(sop_id=read.sop_id, version=read.version, read_at=read.read_at)
