"""Limits of the report endpoint; it takes no sign-in, so every limit here is what keeps it from being used to flood the log."""
from datetime import timedelta

from app.auth.attempts import Rule
from app.csp_reports import messages

# A real report is under 2 KB; the rest of the room is for a long policy text.
MAX_BODY_BYTES = 16 * 1024
MAX_REPORTS_PER_BODY = 20
MAX_FIELD_CHARACTERS = 200
READ_CHUNK_BYTES = 4096

# The browser names the format by the media type: the old one by the first, the Reporting API by the second.
LEGACY_MEDIA_TYPE = "application/csp-report"
REPORTING_API_MEDIA_TYPE = "application/reports+json"
ACCEPTED_MEDIA_TYPES = frozenset({LEGACY_MEDIA_TYPE, REPORTING_API_MEDIA_TYPE, "application/json"})

# Every report counts against one budget for the whole system, because the caller has no account and its address cannot be trusted behind the proxy.
BUDGET = Rule("csp_reports", 120, timedelta(minutes=1), timedelta(minutes=1), timedelta(minutes=10), messages.TOO_MANY_REPORTS, "TOO_MANY_REPORTS")
BUDGET_SUBJECT = "all"
