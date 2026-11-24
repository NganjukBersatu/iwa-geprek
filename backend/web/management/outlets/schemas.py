from datetime import date

from pydantic import BaseModel


class OutletOptionOut(BaseModel):
    id: str
    name: str


class OutletPageOut(BaseModel):
    items: list[OutletOptionOut]
    total: int
    page: int
    size: int


class BranchPeriodOut(BaseModel):
    outlet_id: str
    outlet_name: str
    start: date
    end: date
    adjusted: bool
    sets_pattern: bool
    running: bool
