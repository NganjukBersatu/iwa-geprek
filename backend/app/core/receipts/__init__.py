"""Reads a photographed receipt into store, date, items and total through app.core.ocr; run read in a worker thread."""
from app.core import ocr
from app.core.receipts import parser
from app.core.receipts.reading import ReceiptLine, ReceiptReading

__all__ = ["ReceiptLine", "ReceiptReading", "read"]


def read(content: bytes) -> ReceiptReading:
    return parser.parse(ocr.lines_in(content))
