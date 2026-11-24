from datetime import datetime

from pydantic import BaseModel, Field

from app.employee.sop.schemas import SlideOut
from web.management.sop.constants import MAX_BODY_LENGTH, MAX_SLIDES, MAX_TITLE_LENGTH, MIN_SLIDES


class SlideIn(BaseModel):
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    body: str = Field(default="", max_length=MAX_BODY_LENGTH)


class SopIn(BaseModel):
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    active: bool = True
    outlet_id: str | None = Field(None, description="Empty means every branch")
    slides: list[SlideIn] = Field(min_length=MIN_SLIDES, max_length=MAX_SLIDES, description="Replaces every slide, in this order")
    draft_id: str | None = Field(None, description="The draft this save finishes; it is removed")


class SopOrderIn(BaseModel):
    ids: list[str] = Field(description="Every procedure the account manages, top first")


class ManagedSopSummaryOut(BaseModel):
    id: str
    title: str
    active: bool
    sort_order: int
    version: int
    slide_count: int
    outlet_id: str | None
    outlet_name: str | None
    created_by: str | None
    updated_by: str | None
    updated_at: datetime
    has_draft: bool
    read_count: int = Field(description="People who read this version to the last slide")
    audience_count: int = Field(description="Active accounts that see this procedure in the app")


class ManagedSopOut(ManagedSopSummaryOut):
    slides: list[SlideOut]


class SopMediaOut(BaseModel):
    url: str
    kind: str


class DraftSlideIn(BaseModel):
    """A draft may be unfinished, so nothing in it is required yet; the limits still hold."""

    title: str = Field(default="", max_length=MAX_TITLE_LENGTH)
    body: str = Field(default="", max_length=MAX_BODY_LENGTH)


class DraftContentIn(BaseModel):
    title: str = Field(default="", max_length=MAX_TITLE_LENGTH)
    active: bool = True
    outlet_id: str | None = None
    slides: list[DraftSlideIn] = Field(default_factory=list, max_length=MAX_SLIDES)


class DraftIn(BaseModel):
    id: str | None = Field(None, description="Empty on the first save of a new procedure's draft")
    sop_id: str | None = Field(None, description="Empty while the procedure has never been saved")
    base_version: int | None = None
    content: DraftContentIn


class DraftSummaryOut(BaseModel):
    id: str
    sop_id: str | None
    title: str
    base_version: int | None
    updated_at: datetime


class DraftOut(DraftSummaryOut):
    content: DraftContentIn


class ReaderOut(BaseModel):
    user_id: str
    name: str
    role_name: str | None
    outlet_name: str | None
    read_version: int | None = Field(description="Empty when the person never finished this procedure")
    read_at: datetime | None
    current: bool = Field(description="Read the latest version to the last slide")


class ReaderPageOut(BaseModel):
    items: list[ReaderOut]
    total: int
    page: int
    size: int
    read_count: int
    audience_count: int
    version: int
    title: str
