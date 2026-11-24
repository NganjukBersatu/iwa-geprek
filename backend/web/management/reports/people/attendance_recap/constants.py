from app.core.auth import AnyOf
from web.management.reports import gates

PERMISSION_MANAGE = "kehadiran.kelola"
# Opened from the reports menu or from the schedule screen, so either permission is enough.
RECAP_GATE = AnyOf((PERMISSION_MANAGE, gates.ATTENDANCE))
