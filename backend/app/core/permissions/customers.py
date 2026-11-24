from app.core.permissions.model import Group, Permission, Section

GROUP = Group("customers", "Pelanggan", (
    Section("Pelanggan", (
        Permission("pelanggan.lihat", "Lihat pelanggan", "Membuka daftar dan detail pelanggan."),
    )),
))
