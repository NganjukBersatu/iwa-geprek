"""Turns notice rows into response schemas."""
from app.employee.notices.schemas import NoticeOut
from app.models.notice import Notice


def notice_out(notice: Notice) -> NoticeOut:
    return NoticeOut(
        id=notice.id,
        kind=notice.kind,
        task_kind=notice.task_kind,
        task_id=notice.task_id,
        title=notice.title,
        show_at=notice.show_at,
    )
