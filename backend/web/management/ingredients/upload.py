from app.core.uploads import KIND_PHOTO, UploadRule

RULE = UploadRule(
    kinds=frozenset({KIND_PHOTO}),
    unreadable_note="Foto ulang bahannya.",
    not_saved="Foto bahan gagal disimpan. Coba lagi.",
)
