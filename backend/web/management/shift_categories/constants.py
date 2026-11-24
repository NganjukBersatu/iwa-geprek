from web.management.shift_codes.constants import CATEGORY_KIND, KIND_OFF, KIND_WORK, PERMISSION_MANAGE

__all__ = ["CATEGORY_KIND", "KIND_OFF", "KIND_WORK", "PERMISSION_MANAGE"]

# Sama dengan CHECK di database: jam penuh 00:00 sampai 23:59, tanpa 24:00.
CLOCK_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"
MAX_NAME_LENGTH = 100
NOT_FOUND = 404
FORBIDDEN = 403
CONFLICT = 409
