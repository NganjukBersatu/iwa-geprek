"""Reads what a browser sends about a blocked resource and keeps only what is safe to write to a log.

Everything in a report comes from the caller, so it is cut to a fixed length, stripped of line breaks, and its addresses lose their query and fragment (they can hold tokens).
The sample of the blocked code is dropped on purpose: source code is never logged.
"""
import json
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from app.csp_reports.constants import MAX_FIELD_CHARACTERS, MAX_REPORTS_PER_BODY

NO_VALUE = "-"
CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f  ]")
# A blocked source that is not an address (inline code, eval) or whose whole content would be the address.
KEYWORD_SOURCES = frozenset({"inline", "eval", "wasm-eval", "self", "trusted-types-policy", "trusted-types-sink"})
CONTENT_SCHEMES = frozenset({"data", "blob", "javascript", "about"})
LEGACY_KEY = "csp-report"
VIOLATION_TYPE = "csp-violation"

# The old format writes names with hyphens and the Reporting API in camel case; both are read.
DIRECTIVE_KEYS = ("effective-directive", "effectiveDirective", "violated-directive", "violatedDirective")
BLOCKED_KEYS = ("blocked-uri", "blockedURL")
DOCUMENT_KEYS = ("document-uri", "documentURL")
SOURCE_KEYS = ("source-file", "sourceFile")
LINE_KEYS = ("line-number", "lineNumber")
DISPOSITION_KEYS = ("disposition",)


@dataclass(frozen=True)
class Violation:
    directive: str
    blocked: str
    document: str
    source: str
    line: str
    disposition: str


def _first(report: dict, keys: tuple[str, ...]) -> object:
    for key in keys:
        if key in report:
            return report[key]
    return None


def _text(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return NO_VALUE
    cleaned = CONTROL_CHARACTERS.sub(" ", str(value)).strip()
    return cleaned[:MAX_FIELD_CHARACTERS] or NO_VALUE


def _address(value: object) -> str:
    """The address without its query and fragment; a data, blob, or script address is reduced to its kind."""
    text = _text(value)
    if text == NO_VALUE or text in KEYWORD_SOURCES:
        return text
    try:
        parts = urlsplit(text)
    except ValueError:
        return NO_VALUE
    if parts.scheme in CONTENT_SCHEMES:
        return f"{parts.scheme}:"
    return _text(f"{parts.scheme}://{parts.netloc}{parts.path}" if parts.scheme else parts.path)


def _from_report(report: object) -> Violation | None:
    if not isinstance(report, dict):
        return None
    return Violation(
        directive=_text(_first(report, DIRECTIVE_KEYS)),
        blocked=_address(_first(report, BLOCKED_KEYS)),
        document=_address(_first(report, DOCUMENT_KEYS)),
        source=_address(_first(report, SOURCE_KEYS)),
        line=_text(_first(report, LINE_KEYS)),
        disposition=_text(_first(report, DISPOSITION_KEYS)),
    )


def _bodies(document: object) -> list[object]:
    """The report bodies of either format: one object under a key (old), or a list of typed reports (Reporting API)."""
    if isinstance(document, dict):
        if LEGACY_KEY in document:
            return [document[LEGACY_KEY]]
        return [document.get("body")] if document.get("type") == VIOLATION_TYPE else []
    if isinstance(document, list):
        return [item.get("body") for item in document if isinstance(item, dict) and item.get("type") == VIOLATION_TYPE]
    return []


def read(content: bytes) -> list[Violation]:
    """Raises ValueError when the content is not JSON; reports of other kinds and anything past the limit are skipped."""
    try:
        document = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("not JSON") from error
    found = (_from_report(body) for body in _bodies(document)[:MAX_REPORTS_PER_BODY])
    return [violation for violation in found if violation is not None]
