# Pintu uang untuk semua harga dan laporan: selalu Decimal, dibulatkan hanya lewat round_rupiah.
from decimal import ROUND_HALF_EVEN, Decimal

ZERO = Decimal("0")
RUPIAH = Decimal("1")


def round_rupiah(amount: Decimal) -> Decimal:
    return amount.quantize(RUPIAH, rounding=ROUND_HALF_EVEN)


# Jumlah dari database bisa None, int, float, atau Decimal.
def decimal_of(value) -> Decimal:
    return Decimal(str(value or 0))
