"""Turns procedures and drafts into the admin's response schemas."""
from app.core.http import public_base_url, with_current_sop_media
from app.employee.sop.schemas import SlideOut
from app.models.sop import Sop, SopDraft
from web.management.sop import service
from web.management.sop.schemas import DraftOut, DraftSummaryOut, ManagedSopOut, ManagedSopSummaryOut, ReaderOut, ReaderPageOut
from web.management.sop.service import Names, ReaderPage


def managed_summary_out(sop: Sop, names: Names) -> ManagedSopSummaryOut:
    return ManagedSopSummaryOut(
        id=sop.id,
        title=sop.title,
        active=sop.active,
        sort_order=sop.sort_order,
        version=sop.version,
        slide_count=len(sop.slides),
        outlet_id=sop.outlet_id,
        outlet_name=names.outlets.get(sop.outlet_id) if sop.outlet_id else None,
        created_by=names.user.get(sop.created_by_id) if sop.created_by_id else None,
        updated_by=names.user.get(sop.updated_by_id) if sop.updated_by_id else None,
        updated_at=sop.updated_at,
        has_draft=sop.id in names.drafted,
        read_count=names.current_reads.get(sop.id, 0),
        audience_count=names.audience_of(sop),
    )


def managed_out(sop: Sop, names: Names) -> ManagedSopOut:
    base = public_base_url()
    return ManagedSopOut(
        **managed_summary_out(sop, names).model_dump(),
        slides=[SlideOut(id=slide.id, title=slide.title, body=with_current_sop_media(slide.body, base)) for slide in sop.slides],
    )


def draft_summary_out(draft: SopDraft) -> DraftSummaryOut:
    return DraftSummaryOut(
        id=draft.id,
        sop_id=draft.sop_id,
        title=service.draft_content(draft).title,
        base_version=draft.base_version,
        updated_at=draft.updated_at,
    )


def draft_out(draft: SopDraft) -> DraftOut:
    content = service.draft_content(draft)
    base = public_base_url()
    slides = [slide.model_copy(update={"body": with_current_sop_media(slide.body, base)}) for slide in content.slides]
    return DraftOut(**draft_summary_out(draft).model_dump(), content=content.model_copy(update={"slides": slides}))


def reader_page_out(page: ReaderPage) -> ReaderPageOut:
    return ReaderPageOut(
        items=[
            ReaderOut(
                user_id=row.user_id,
                name=row.name,
                role_name=row.role_name,
                outlet_name=row.outlet_name,
                read_version=row.version,
                read_at=row.read_at,
                current=row.version is not None and row.version >= page.version,
            )
            for row in page.rows
        ],
        total=page.total,
        page=page.page,
        size=page.size,
        read_count=page.current,
        audience_count=page.audience,
        version=page.version,
        title=page.title,
    )
