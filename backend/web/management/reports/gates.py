"""The one table of who may see which report and which dashboard card; routes and screens take their gate from here."""
from app.core.auth import AnyOf, Gate

OVERVIEW = "laporan.overview"
BUSY_SALES = "laporan.ramai_penjualan"
BUSY_PRODUCTS = "laporan.ramai_produk"
CATEGORIES = "laporan.kategori"
OPTIONS = "laporan.varian_ekstra"
PROMOS = "laporan.promo"
VOIDS = "laporan.batal"
VISITORS = "laporan.pengunjung"
INGREDIENT_STOCK = "laporan.stok_bahan"
STOCK_TURNOVER = "laporan.perputaran"
ATTENDANCE = "laporan.kehadiran"
MARGIN = "laporan.margin"
STATION_PERFORMANCE = "laporan.kinerja_stasiun"

# One permission for each card of the dashboard; the dashboard itself opens for whoever holds at least one.
SUMMARY = "laporan.ringkasan"
TREND = "laporan.tren"
PROFIT_LOSS = "laporan.laba_rugi"
INVENTORY_VALUE = "laporan.nilai_persediaan"
CASHIERS = "laporan.kasir"
CUSTOMERS = "laporan.pelanggan"
COMPARISON = "laporan.perbandingan"
TRANSACTIONS = "laporan.transaksi"

DASHBOARD_CARDS: tuple[str, ...] = (SUMMARY, TREND, PROFIT_LOSS, INVENTORY_VALUE, CASHIERS, CUSTOMERS, COMPARISON, TRANSACTIONS)

DASHBOARD: Gate = AnyOf(DASHBOARD_CARDS)
# The transaction list feeds both the dashboard and Overview Keuangan.
TRANSACTION_LIST: Gate = AnyOf((OVERVIEW, TRANSACTIONS))

# Writing in the reports area: matching the non-cash figures to the system's own record.
VALIDATE_NON_CASH = "laporan.validasi"
