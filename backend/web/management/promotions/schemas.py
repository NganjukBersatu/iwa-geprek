from pydantic import BaseModel

from app.core.catalog.promotion_schemas import AnnouncementOut, PromoOut


class PromoPageOut(BaseModel):
    items: list[PromoOut]
    total: int
    page: int
    size: int


class AnnouncementPageOut(BaseModel):
    items: list[AnnouncementOut]
    total: int
    page: int
    size: int
