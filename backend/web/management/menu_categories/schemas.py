from pydantic import BaseModel, Field

from web.management.menu_categories.constants import MAX_NAME_LENGTH


class MenuCategoryCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)


class MenuCategoryUpdateIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)


class MenuCategoryRecordOut(BaseModel):
    id: str
    name: str
    menu_count: int = Field(description="Menus filed under this category")
    station_name: str | None = Field(description="The station that makes this category by default; empty when none is set")
