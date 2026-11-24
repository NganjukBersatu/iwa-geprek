"""The one door for reading printed text from a photo; recognition runs on this server, so the photo never leaves it.

A feature turns the lines into its own fields (app.core.receipts does it for receipts). Callers run lines_in in a worker
thread (asyncio.to_thread), since one photo takes a second or more of CPU.
"""
from app.core.errors import SERVER_ERROR, DomainError
from app.core.ocr import engine, layout
from app.core.ocr.engine import TextBox

UNREADABLE = "Foto tidak bisa dibaca. Isi rinciannya secara manual."

__all__ = ["TextBox", "boxes_in", "lines_in"]


def boxes_in(content: bytes) -> list[TextBox]:
    """Every piece of text with its position, for a feature that needs the layout itself."""
    try:
        return engine.recognize(content)
    except Exception as error:  # noqa: BLE001
        raise DomainError(UNREADABLE, status=SERVER_ERROR) from error


def lines_in(content: bytes) -> list[str]:
    """The text top to bottom, pieces printed at the same height joined left to right."""
    return layout.lines_of(boxes_in(content))
