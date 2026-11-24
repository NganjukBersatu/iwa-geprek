PERMISSION_VIEW = "jadwal.lihat"
PERMISSION_MANAGE = "jadwal.kelola"

# The longest range one request may read; schedules are planned by week or month.
MAX_RANGE_DAYS = 62
DAYS_IN_WEEK = 7
MAX_NOTE_LENGTH = 300

MINUTES_PER_HOUR = 60
MINUTES_PER_DAY = 24 * MINUTES_PER_HOUR

# A shift lasts at most one day, so an assignment still running started today or yesterday.
LOOKBACK_DAYS = 1

# Owner rule: a clock-in opens this many minutes before the assignment starts.
CLOCK_IN_EARLY_MINUTES = 30

# Owner rule: a self-made schedule may only use a shift code starting this many minutes before or after now.
SELF_SCHEDULE_RANGE_MINUTES = 30
