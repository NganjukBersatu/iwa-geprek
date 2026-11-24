package id.kongstudio.cafe.feature.cashier

import androidx.compose.runtime.Stable
import androidx.compose.runtime.mutableStateListOf

/** Sama dengan batas catatan per baris di server, supaya pesanan (juga yang antre offline) tidak ditolak karena catatan terlalu panjang. */
internal const val LineNoteMaxLength = 255

/** Satu baris pesanan; pilihan yang berbeda untuk menu yang sama menjadi baris terpisah. */
internal data class CartEntry(
    val menuId: String,
    val variantIds: List<String>,
    /** Id ekstra ke jumlah per porsi. */
    val extras: Map<String, Int>,
    val note: String?,
    val quantity: Int,
) {
    val key: String
        get() = listOf(
            menuId,
            variantIds.sorted().joinToString(","),
            extras.entries.sortedBy { it.key }.joinToString(",") { "${it.key}x${it.value}" },
            note.orEmpty(),
        ).joinToString("|")
}

@Stable
internal class CartState {
    private val entries = mutableStateListOf<CartEntry>()

    val itemCount: Int get() = entries.sumOf { it.quantity }

    val isEmpty: Boolean get() = entries.isEmpty()

    /** Jumlah semua baris milik satu menu, apa pun pilihannya. */
    fun quantityOf(menuId: String): Int = entries.filter { it.menuId == menuId }.sumOf { it.quantity }

    fun add(
        item: CashierItem,
        variantIds: List<String> = emptyList(),
        extras: Map<String, Int> = emptyMap(),
        note: String? = null,
    ) {
        val fresh = CartEntry(item.id, variantIds, extras.filterValues { it > 0 }, note?.trim()?.take(LineNoteMaxLength)?.ifEmpty { null }, 1)
        val index = entries.indexOfFirst { it.key == fresh.key }
        if (index < 0) {
            entries.add(fresh)
        } else {
            entries[index] = entries[index].copy(quantity = entries[index].quantity + 1)
        }
    }

    fun increase(key: String) {
        val index = entries.indexOfFirst { it.key == key }
        if (index >= 0) entries[index] = entries[index].copy(quantity = entries[index].quantity + 1)
    }

    fun decrease(key: String) {
        val index = entries.indexOfFirst { it.key == key }
        if (index < 0) return
        val current = entries[index]
        if (current.quantity <= 1) entries.removeAt(index) else entries[index] = current.copy(quantity = current.quantity - 1)
    }

    /** Mengganti catatan satu baris; bila hasilnya sama persis dengan baris lain, keduanya digabung. */
    fun setNote(key: String, note: String?) {
        val index = entries.indexOfFirst { it.key == key }
        if (index < 0) return
        val updated = entries[index].copy(note = note?.trim()?.take(LineNoteMaxLength)?.ifEmpty { null })
        if (updated.key == key) return
        val twin = entries.indexOfFirst { it.key == updated.key }
        if (twin < 0) {
            entries[index] = updated
        } else {
            entries[twin] = entries[twin].copy(quantity = entries[twin].quantity + updated.quantity)
            entries.removeAt(index)
        }
    }

    /** Mengurangi satu porsi menu sederhana langsung dari kartunya. */
    fun decreaseMenu(menuId: String) {
        val index = entries.indexOfLast { it.menuId == menuId }
        if (index >= 0) decrease(entries[index].key)
    }

    fun clear() = entries.clear()

    /** Mengisi dari simpanan hanya bila keranjang masih kosong, supaya pilihan kasir yang sudah masuk tidak tertimpa. */
    fun restore(saved: List<CartEntry>) {
        if (entries.isEmpty()) entries.addAll(saved)
    }

    /** Membuang baris yang menu, varian, atau ekstranya sudah tidak ada di katalog, supaya tidak ikut terkirim tanpa terlihat. */
    fun retainValid(catalog: Map<String, CashierItem>) {
        entries.removeAll { entry ->
            val item = catalog[entry.menuId] ?: return@removeAll true
            val variants = item.variants.flatMap { group -> group.options.map { it.id } }.toSet()
            val extras = item.extras.map { it.id }.toSet()
            !variants.containsAll(entry.variantIds) || !extras.containsAll(entry.extras.keys)
        }
    }

    /** Baris yang menunya sudah tidak ada di katalog dibuang dari tampilan. */
    fun lines(catalog: Map<String, CashierItem>): List<CartLine> =
        entries.mapNotNull { entry ->
            val item = catalog[entry.menuId] ?: return@mapNotNull null
            val variantNames = item.variants.flatMap { group ->
                group.options.filter { it.id in entry.variantIds }.map { it.name }
            }
            val extraParts = item.extras.mapNotNull { extra ->
                entry.extras[extra.id]?.let { count -> extra to count }
            }
            val extraTotal = extraParts.sumOf { (extra, count) -> extra.price * count }
            CartLine(
                key = entry.key,
                item = item,
                quantity = entry.quantity,
                details = variantNames + extraParts.map { (extra, count) ->
                    if (count > 1) "${extra.name} x$count" else extra.name
                },
                note = entry.note,
                unitPrice = item.price + extraTotal,
                variants = variantNames,
                extras = extraParts.map { (extra, count) -> PickedExtra(extra.name, count, extra.price) },
            )
        }

    /** Pilihan mentah untuk dikirim ke server. */
    fun entries(): List<CartEntry> = entries.toList()
}
