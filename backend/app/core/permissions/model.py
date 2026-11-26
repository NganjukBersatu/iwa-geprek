from dataclasses import dataclass


@dataclass(frozen=True)
class Permission:
    """[label] and [description] are written from what it lets a person do."""

    key: str
    label: str
    description: str
    default_for_new_role: bool = False
    # Dicentang oleh tombol "Mulai dari contoh Kasir" di form Tambah Peran: izin minimum untuk berjualan di perangkat kasir.
    in_cashier_example: bool = False


@dataclass(frozen=True)
class Section:
    name: str
    permissions: tuple[Permission, ...]


@dataclass(frozen=True)
class Group:
    key: str
    name: str
    sections: tuple[Section, ...]
