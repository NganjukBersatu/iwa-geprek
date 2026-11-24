"""What the rating service hands to the mappers."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Component:
    """One measure: `counted` of `of` items (minutes for attendance), as a percent; None when there is nothing to measure."""

    key: str
    percent: float | None
    counted: int
    of: int


@dataclass(frozen=True)
class Group:
    key: str
    score: float | None
    components: list[Component]


@dataclass(frozen=True)
class Rating:
    stars: float | None
    score: float | None
    groups: list[Group]
