"""What the procedure service receives from the routes."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SlideContent:
    title: str
    body: str


@dataclass(frozen=True)
class SopContent:
    title: str
    active: bool
    outlet_id: str | None
    slides: tuple[SlideContent, ...]
