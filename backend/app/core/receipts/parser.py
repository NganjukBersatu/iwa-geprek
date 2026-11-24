"""Turns the lines of an Indonesian receipt into store, date, items and total; anything unsure is left out rather than guessed."""
import re
from datetime import date
from decimal import Decimal

from app.core.receipts.reading import ReceiptLine, ReceiptReading

MIN_AMOUNT = Decimal(100)
MAX_NAME_LENGTH = 255
STORE_SEARCH_LINES = 6
MIN_LETTERS = 2
CENTS = Decimal(100)
CENTURY = 2000
TWO_DIGIT_YEAR = 100

NUMBER = r"(?:\d{1,3}(?:[.,]\d{3})+|\d+)(?:[.,]\d{2})?"
MONEY = re.compile(rf"(?:Rp\.?\s*)?({NUMBER})", re.IGNORECASE)
TRAILING_MONEY = re.compile(rf"^(?P<head>.*?)(?:^|(?<=[\s:]))(?:Rp\.?\s*)?(?P<amount>{NUMBER})\s*-?$", re.IGNORECASE)
ONLY_MONEY = re.compile(rf"^(?:Rp\.?\s*)?(?P<amount>{NUMBER})$", re.IGNORECASE)
QUANTITY_LINE = re.compile(rf"^(?P<quantity>\d{{1,3}})(?:\s*[xX@*]\s*|\s+)(?:Rp\.?\s*)?{NUMBER}\s+(?:Rp\.?\s*)?(?P<amount>{NUMBER})$", re.IGNORECASE)
QUANTITY_IN_NAME = re.compile(rf"^(?P<name>.*[A-Za-z].*?)\s+(?P<quantity>\d{{1,3}})(?:\s*[xX@*]\s*|\s+)(?:Rp\.?\s*)?{NUMBER}$", re.IGNORECASE)
LEADING_CODE = re.compile(r"^(?:\d{4,}\s+)+")
LETTERS = re.compile(r"[A-Za-z]")
OCR_ZERO = re.compile(r"(?<=\d)[Oo]|[Oo](?=\d)")

DAY_FIRST = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4}|\d{2})\b")
YEAR_FIRST = re.compile(r"\b(\d{4})[./-](\d{1,2})[./-](\d{1,2})\b")
MONTH_NAMED = re.compile(r"\b(\d{1,2})[\s-]+([A-Za-z]{3})[A-Za-z]*\.?[\s-]+(\d{4}|\d{2})\b")
MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "may": 5, "jun": 6, "jul": 7,
    "agu": 8, "agt": 8, "aug": 8, "sep": 9, "okt": 10, "oct": 10, "nov": 11, "des": 12, "dec": 12,
}

# (label, rank): the first label found names the line, so longer ones come before the words they contain; the lower rank wins between lines.
TOTAL_LABELS = (
    ("sub total", 5),
    ("subtotal", 5),
    ("grand total", 0),
    ("total bayar", 1),
    ("total belanja", 1),
    ("total harga", 1),
    ("total tagihan", 1),
    ("harga jual", 2),
    ("total", 3),
    ("jumlah", 4),
)
NOT_TOTAL = ("total diskon", "total disc", "total hemat", "total potongan")
NOT_ITEM = re.compile(
    r"\b(?:tunai|cash|kembali|kembalian|change|bayar|dibayar|payment|ppn|pajak|tax|pb1|diskon|disc|discount|potongan|hemat|"
    r"voucher|service|servis|debit|kredit|credit|qris|kartu|card|edc|ovo|gopay|shopeepay|poin|point|saldo|member|dpp|item|"
    r"qty|kasir|cashier|telp|tel|npwp|struk|nota|terima kasih|thank|jl|jalan|tanggal|tgl|waktu|ref|trx|transaksi|pembulatan|rounding)\b"
)
NOT_STORE = re.compile(r"\b(?:struk|nota|receipt|invoice|faktur|jl|jalan|telp|tel|npwp|no|tanggal|tgl|kasir|www|http)\b")


def _normal(text: str) -> str:
    return OCR_ZERO.sub("0", " ".join(text.split()))


def money_of(text: str) -> Decimal | None:
    found = MONEY.fullmatch(text.strip())
    if found is None:
        return None
    number = found.group(1)
    cents = Decimal(0)
    # A trailing separator with exactly two digits is cents, as in 12.500,00; three digits is always thousands.
    if len(number) > 3 and number[-3] in ".," and number[-2:].isdigit():
        cents = Decimal(number[-2:]) / CENTS
        number = number[:-3]
    return Decimal(re.sub(r"[.,]", "", number)) + cents


def _letters(text: str) -> int:
    return len(LETTERS.findall(text))


def _total_rank(lowered: str) -> int | None:
    if any(label in lowered for label in NOT_TOTAL):
        return None
    return next((rank for label, rank in TOTAL_LABELS if re.search(rf"\b{label}\b", lowered)), None)


def _name(text: str) -> str:
    return LEADING_CODE.sub("", text).strip(" :.-*").strip()[:MAX_NAME_LENGTH]


def _store(lines: list[str]) -> str | None:
    for line in lines[:STORE_SEARCH_LINES]:
        lowered = line.lower()
        if _letters(line) >= MIN_LETTERS * 2 and not NOT_STORE.search(lowered) and TRAILING_MONEY.match(line) is None:
            return line.strip(" :.-*")[:MAX_NAME_LENGTH]
    return None


def _date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year + CENTURY if year < TWO_DIGIT_YEAR else year, month, day)
    except ValueError:
        return None


def _bought_on(lines: list[str]) -> date | None:
    for line in lines:
        if found := YEAR_FIRST.search(line):
            if parsed := _date(int(found.group(1)), int(found.group(2)), int(found.group(3))):
                return parsed
        if found := DAY_FIRST.search(line):
            if parsed := _date(int(found.group(3)), int(found.group(2)), int(found.group(1))):
                return parsed
        if (found := MONTH_NAMED.search(line)) and (month := MONTHS.get(found.group(2).lower())):
            if parsed := _date(int(found.group(3)), month, int(found.group(1))):
                return parsed
    return None


def parse(raw_lines: list[str]) -> ReceiptReading:
    lines = [line for line in (_normal(raw) for raw in raw_lines) if line]
    items: list[ReceiptLine] = []
    total: Decimal | None = None
    total_rank: int | None = None
    pending_name: str | None = None
    pending_total_rank: int | None = None
    items_done = False

    for line in lines:
        lowered = line.lower()
        rank = _total_rank(lowered)
        trailing = TRAILING_MONEY.match(line)
        amount = money_of(trailing.group("amount")) if trailing else None

        if rank is not None:
            found = amount is not None and amount >= MIN_AMOUNT
            # Payment lines follow the total, so nothing after it is an item; a label without a figure before any item is a column heading.
            items_done = items_done or found or bool(items)
            pending_name = None
            if found and amount is not None:
                if total_rank is None or rank < total_rank:
                    total, total_rank = amount, rank
                pending_total_rank = None
            else:
                pending_total_rank = rank
            continue

        if pending_total_rank is not None:
            # The label and its amount were read as separate lines.
            only = ONLY_MONEY.match(line)
            figure = money_of(only.group("amount")) if only else None
            waiting, pending_total_rank = pending_total_rank, None
            if figure is not None and figure >= MIN_AMOUNT:
                if total_rank is None or waiting < total_rank:
                    total, total_rank = figure, waiting
                continue

        if items_done or NOT_ITEM.search(lowered):
            pending_name = None
            continue

        quantity_line = QUANTITY_LINE.match(line)
        if quantity_line and pending_name:
            figure = money_of(quantity_line.group("amount"))
            if figure is not None and figure >= MIN_AMOUNT:
                items.append(ReceiptLine(pending_name, figure, int(quantity_line.group("quantity"))))
            pending_name = None
            continue

        only = ONLY_MONEY.match(line)
        if only and pending_name:
            figure = money_of(only.group("amount"))
            if figure is not None and figure >= MIN_AMOUNT:
                items.append(ReceiptLine(pending_name, figure, None))
            pending_name = None
            continue

        if trailing and amount is not None and amount >= MIN_AMOUNT and _letters(trailing.group("head")) >= MIN_LETTERS:
            head = trailing.group("head").strip()
            quantity: int | None = None
            if in_name := QUANTITY_IN_NAME.match(head):
                head, quantity = in_name.group("name"), int(in_name.group("quantity"))
            if name := _name(head):
                items.append(ReceiptLine(name, amount, quantity))
            pending_name = None
            continue

        pending_name = _name(line) if _letters(line) >= MIN_LETTERS else None

    return ReceiptReading(
        store=_store(lines),
        bought_on=_bought_on(lines),
        total=total,
        items=tuple(items),
        text=tuple(lines),
    )
