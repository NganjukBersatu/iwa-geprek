from pydantic import BaseModel


class ComponentOut(BaseModel):
    key: str
    percent: float | None
    counted: int
    of: int


class RatingGroupOut(BaseModel):
    key: str
    score: float | None
    components: list[ComponentOut]


class RatingOut(BaseModel):
    stars: float | None
    score: float | None
    groups: list[RatingGroupOut]
