from datetime import datetime

from pydantic import BaseModel, Field


class SlideOut(BaseModel):
    id: str
    title: str
    body: str


class SopSummaryOut(BaseModel):
    id: str
    title: str
    version: int
    slide_count: int
    updated_at: datetime
    outlet_name: str | None = None


class SopOut(SopSummaryOut):
    slides: list[SlideOut]


class SopReadIn(BaseModel):
    version: int = Field(ge=1, description="The version shown when the last slide was finished")


class SopReadOut(BaseModel):
    sop_id: str
    version: int
    read_at: datetime
