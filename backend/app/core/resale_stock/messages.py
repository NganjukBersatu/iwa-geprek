"""Every sentence the resold stock ledger can raise."""

MENU_NOT_FOUND = "Menu tidak ditemukan"
ZERO_ADJUSTMENT = "Jumlah penyesuaian tidak boleh nol"


def not_marked(name: str) -> str:
    return f"'{name}' belum ditandai sebagai barang jual-ulang. Tandai dulu lewat Kelola barang, atau catat sebagai bahan baku."
