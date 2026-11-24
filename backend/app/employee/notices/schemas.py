from datetime import datetime

from pydantic import BaseModel


class NoticeOut(BaseModel):
    id: str
    kind: str
    task_kind: str | None
    task_id: str | None
    title: str
    show_at: datetime
