"""The text recognizer: loaded on the first photo, then shared, reading one photo at a time so memory stays flat."""
import threading
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING

from PIL import Image, ImageOps

if TYPE_CHECKING:
    from rapidocr import RapidOCR

ENGINE_PARAMS = {"Global.log_level": "warning"}


@dataclass(frozen=True)
class TextBox:
    text: str
    left: float
    right: float
    top: float
    bottom: float


_lock = threading.Lock()
_engine: "RapidOCR | None" = None


def _recognizer() -> "RapidOCR":
    global _engine
    if _engine is None:
        from rapidocr import RapidOCR

        _engine = RapidOCR(params=ENGINE_PARAMS)
    return _engine


def recognize(content: bytes) -> list[TextBox]:
    with Image.open(BytesIO(content)) as opened:
        upright = ImageOps.exif_transpose(opened).convert("RGB")
    with _lock:
        result = _recognizer()(upright)
    if result.boxes is None or not result.txts:
        return []
    found: list[TextBox] = []
    for points, text in zip(result.boxes, result.txts):
        cleaned = str(text).strip()
        if not cleaned:
            continue
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        found.append(TextBox(cleaned, min(xs), max(xs), min(ys), max(ys)))
    return found
