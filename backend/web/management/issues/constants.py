"""Every limit of the detectors, set by the owner on 25 Oct 2026; a change here changes what the page reports."""
from decimal import Decimal

# A past event is shown for this many days, today included, then it leaves the list by itself.
EVENT_DAYS = 7
# Money not yet handed over or checked is looked for this far back.
MONEY_LOOKBACK_DAYS = 31

CASH_DIFFERENCE_LIMIT = Decimal(0)
SESSION_OPEN_HOURS = 16
DEPOSIT_LATE_DAYS = 2
NON_CASH_LATE_DAYS = 1
VOIDS_PER_CASHIER_DAY = 3
PRICE_JUMP_PERCENT = Decimal(20)
IDLE_INGREDIENT_DAYS = 30
UNSOLD_MENU_DAYS = 30
PROMO_ENDING_DAYS = 3
PROMO_UNUSED_DAYS = 7
SCHEDULE_AHEAD_DAYS = 7
# An empty schedule this many days ahead or sooner is a problem; later it is a warning.
SCHEDULE_URGENT_DAYS = 1
LATE_REPEATED_COUNT = 3
LATE_REPEATED_DAYS = 30
DEVICE_IDLE_DAYS = 3

# Words that only name a temperature or size; two menus whose names differ only by them belong in one menu with a variant.
VARIANT_WORDS = frozenset({"panas", "dingin", "hot", "ice", "iced", "es", "regular", "large"})

PERMISSION_SESSIONS = "shift.lihat_semua"
PERMISSION_DEPOSITS = "setoran.lihat"
PERMISSION_APPROVE_VOID = "order.void.setujui"
PERMISSION_STOCK = "stok.lihat"
PERMISSION_INGREDIENTS = "bahan.kelola"
PERMISSION_RECIPE_COST = "resep.detail"
PERMISSION_RECIPES = "resep.kelola"
PERMISSION_MENU = "menu.kelola"
PERMISSION_PROMO = "promo.kelola"
PERMISSION_ATTENDANCE = "kehadiran.kelola"
PERMISSION_SCHEDULE = "jadwal.lihat"
PERMISSION_USER = "karyawan.kelola"
PERMISSION_TASKS = "tugas.lihat"
PERMISSION_DEVICES = "cabang.kelola"
