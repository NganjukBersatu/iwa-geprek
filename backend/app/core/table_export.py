"""The one door for downloading a table as CSV, Excel or PDF; a screen hands over its title, its columns and its rows as shown, and gets a file back."""
import csv
import re
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO, StringIO

CSV = "csv"
XLSX = "xlsx"
PDF = "pdf"
FORMATS = (CSV, XLSX, PDF)

MEDIA_TYPES = {
    CSV: "text/csv; charset=utf-8",
    XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    PDF: "application/pdf",
}

MAX_ROWS = 5000
MAX_COLUMNS = 30
MAX_CELL_CHARS = 500
CSV_DELIMITER = ";"
SHEET_TITLE_LENGTH = 31
XLSX_MIN_WIDTH = 8
XLSX_MAX_WIDTH = 50
PDF_WIDE_COLUMNS = 6
PDF_MARGIN = 10
PDF_MIN_WEIGHT = 6
PDF_MAX_WEIGHT = 40
PDF_WEIGHT_SAMPLE = 200
BRAND_RGB = (0x2D, 0x6A, 0x4F)
WIB_LABEL = "Dibuat {at:%d/%m/%Y %H:%M} WIB"

# A cell that starts like a formula is read by a spreadsheet as one, so it is marked as plain text.
FORMULA_START = ("=", "+", "@", "\t", "\r")
PDF_REPLACEMENTS = str.maketrans({"–": "-", "—": "-", "‘": "'", "’": "'", "“": '"', "”": '"', "•": "-", "…": "...", " ": " "})


@dataclass(frozen=True)
class ExportColumn:
    label: str
    align: str = "left"


@dataclass(frozen=True)
class Exported:
    content: bytes
    media_type: str
    extension: str


def _safe(text: str) -> str:
    cell = text[:MAX_CELL_CHARS]
    dash_word = cell.startswith("-") and len(cell) > 1 and cell[1].isalpha() and not cell.startswith("-Rp")
    return f"'{cell}" if cell.startswith(FORMULA_START) or dash_word else cell


def filename(title: str, extension: str, day) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "data"
    return f"{slug}-{day:%Y-%m-%d}.{extension}"


def render(fmt: str, title: str, columns: list[ExportColumn], rows: list[list[str]], generated_at: datetime) -> Exported:
    if fmt == CSV:
        return Exported(_csv(columns, rows), MEDIA_TYPES[CSV], CSV)
    if fmt == XLSX:
        return Exported(_xlsx(title, columns, rows, generated_at), MEDIA_TYPES[XLSX], XLSX)
    if fmt == PDF:
        return Exported(_pdf(title, columns, rows, generated_at), MEDIA_TYPES[PDF], PDF)
    raise ValueError(fmt)


def _csv(columns: list[ExportColumn], rows: list[list[str]]) -> bytes:
    """A byte order mark and semicolons, which is what Excel with Indonesian settings opens correctly."""
    out = StringIO()
    writer = csv.writer(out, delimiter=CSV_DELIMITER, lineterminator="\r\n")
    writer.writerow([_safe(column.label) for column in columns])
    for row in rows:
        writer.writerow([_safe(cell) for cell in row])
    return ("﻿" + out.getvalue()).encode("utf-8")


def _xlsx(title: str, columns: list[ExportColumn], rows: list[list[str]], generated_at: datetime) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = re.sub(r"[\[\]:*?/\\]", " ", title).strip()[:SHEET_TITLE_LENGTH] or "Data"
    sheet.append([_safe(title)])
    sheet.append([WIB_LABEL.format(at=generated_at)])
    sheet.append([])
    sheet["A1"].font = Font(bold=True, size=14)
    sheet["A2"].font = Font(italic=True, color="64748B")

    header_row = 4
    sheet.append([_safe(column.label) for column in columns])
    fill = PatternFill("solid", start_color="%02X%02X%02X" % BRAND_RGB)
    for index, column in enumerate(columns, start=1):
        head = sheet.cell(row=header_row, column=index)
        head.font = Font(bold=True, color="FFFFFF")
        head.fill = fill
        head.alignment = Alignment(horizontal="right" if column.align == "right" else "left", vertical="center")
    for row in rows:
        sheet.append([_safe(cell) for cell in row])
    for index, column in enumerate(columns, start=1):
        longest = max([len(column.label), *(len(row[index - 1]) for row in rows)])
        sheet.column_dimensions[get_column_letter(index)].width = min(max(longest + 2, XLSX_MIN_WIDTH), XLSX_MAX_WIDTH)
        if column.align == "right":
            for line in range(header_row + 1, header_row + 1 + len(rows)):
                sheet.cell(row=line, column=index).alignment = Alignment(horizontal="right")
    sheet.freeze_panes = sheet.cell(row=header_row + 1, column=1)
    out = BytesIO()
    workbook.save(out)
    return out.getvalue()


def _latin(text: str) -> str:
    """The built-in PDF fonts only hold Latin-1, so a character outside it becomes a question mark instead of breaking the file."""
    return _safe(text).translate(PDF_REPLACEMENTS).encode("latin-1", "replace").decode("latin-1")


def _pdf(title: str, columns: list[ExportColumn], rows: list[list[str]], generated_at: datetime) -> bytes:
    from fpdf import FPDF
    from fpdf.fonts import FontFace

    class Page(FPDF):
        def footer(self) -> None:
            self.set_y(-12)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 116, 139)
            self.cell(0, 5, f"Halaman {self.page_no()} dari {{nb}}", align="C")

    wide = len(columns) > PDF_WIDE_COLUMNS
    pdf = Page(orientation="L" if wide else "P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_margins(PDF_MARGIN, PDF_MARGIN, PDF_MARGIN)
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, _latin(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 5, WIB_LABEL.format(at=generated_at), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_text_color(30, 41, 59)
    pdf.set_font("Helvetica", "", 8 if wide else 9)

    sample = rows[:PDF_WEIGHT_SAMPLE]
    weights = [
        min(max(max([len(column.label), *(len(row[index]) for row in sample)]), PDF_MIN_WEIGHT), PDF_MAX_WEIGHT)
        for index, column in enumerate(columns)
    ]
    heading = FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=BRAND_RGB)
    with pdf.table(
        col_widths=tuple(weights),
        text_align=tuple("RIGHT" if column.align == "right" else "LEFT" for column in columns),
        headings_style=heading,
        line_height=5.5,
        borders_layout="HORIZONTAL_LINES",
    ) as table:
        header = table.row()
        for column in columns:
            header.cell(_latin(column.label))
        for line in rows:
            row = table.row()
            for cell in line:
                row.cell(_latin(cell))
    return bytes(pdf.output())
