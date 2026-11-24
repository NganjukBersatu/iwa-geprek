"""Every sentence shown to the admin on the ingredients screen, in one place."""

NOT_FOUND = "Bahan tidak ditemukan di cabang ini"
NAME_REQUIRED = "Nama bahan tidak boleh kosong"
UNIT_UNKNOWN = "Satuan tidak ditemukan."
CATEGORY_UNKNOWN = "Kategori tidak ditemukan."
SHARED_ELSEWHERE = "Bahan ini dipakai di cabang lain. Nama dan satuannya hanya bisa diubah pemilik lintas-cabang."
STILL_USED = "Bahan masih dipakai di tempat lain"
INDIRECT_STILL_IN_RECIPES = "Bahan ini masih ada di {count} baris resep. Lepas dari resep dulu sebelum ditandai tidak langsung."


def already_in_branch(name: str) -> str:
    return f"Bahan '{name}' sudah ada di cabang ini"


def unit_clash(name: str, kept_unit: str, asked_unit: str) -> str:
    return f"Bahan '{name}' sudah ada di katalog dengan satuan '{kept_unit}', bukan '{asked_unit}'. Pakai satuan yang sama, atau beri nama yang berbeda."


def catalog_name_taken(name: str) -> str:
    return f"Nama '{name}' sudah dipakai bahan lain di katalog."


def branch_name_taken(name: str, branches: list[str]) -> str:
    return f"Nama '{name}' sudah dipakai bahan lain di cabang: {', '.join(branches)}."

OWNER_ONLY = "Hanya pemilik lintas-cabang yang bisa menambah bahan ke semua cabang."
NO_ACTIVE_BRANCH = "Tidak ada cabang aktif"
ALREADY_LINKED = "Bahan ini sudah tertaut ke katalog"
PICK_ONE_ENTRY = "Pilih salah satu: entri katalog yang ada, atau buat entri baru"
CATALOG_NOT_FOUND = "Entri katalog tidak ditemukan"


def link_unit_clash(name: str, unit: str, entry_name: str, entry_unit: str) -> str:
    return f"Satuan bahan ini '{unit}', sedangkan '{entry_name}' di katalog memakai '{entry_unit}'. Samakan satuannya dulu, atau pilih entri lain."


def branch_has_entry(name: str) -> str:
    return f"Cabang ini sudah punya bahan lain yang tertaut ke '{name}'"


def catalog_in_use(name: str, branches: int) -> str:
    return f"Entri katalog \"{name}\" masih dipakai bahan di {branches} cabang. Hapus dulu bahan tersebut, baru entrinya bisa dihapus."
