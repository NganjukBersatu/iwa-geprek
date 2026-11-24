package id.kongstudio.cafe.feature.cashier

import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.offline.OfflineStore
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

private const val DraftKeyPrefix = "cashier.cart."

// Keranjang yang ditinggal lebih dari dua jam dianggap sisa tamu atau shift lalu, bukan pesanan yang masih menunggu.
private const val DraftMaxAgeSeconds = 2 * 60 * 60L

private val DraftJson = Json { ignoreUnknownKeys = true }

@Serializable
private class DraftEntry(
    val menuId: String,
    val variantIds: List<String>,
    val extras: Map<String, Int>,
    val note: String?,
    val quantity: Int,
)

/** Menyimpan keranjang yang belum dibayar per karyawan di tablet, supaya pesanan tamu tidak hilang saat aplikasi ditutup atau tablet mati. */
internal class CartDraftStore(private val store: OfflineStore, userId: String) {
    private val key = DraftKeyPrefix + userId

    suspend fun load(): List<CartEntry> {
        // Simpanan rusak atau tidak terbaca cukup berarti keranjang mulai kosong.
        val cached = runCatching { store.getCache(key) }.getOrNull() ?: return emptyList()
        if (ServerClock.nowEpochSeconds() - cached.savedEpoch > DraftMaxAgeSeconds) return emptyList()
        return runCatching { DraftJson.decodeFromString<List<DraftEntry>>(cached.body) }.getOrNull().orEmpty()
            .filter { it.quantity > 0 }
            .map { CartEntry(it.menuId, it.variantIds, it.extras, it.note, it.quantity) }
    }

    suspend fun save(entries: List<CartEntry>) {
        // Gagal menyimpan hanya berarti keranjang ini tidak pulih setelah aplikasi ditutup; penjualan tidak terhenti.
        runCatching {
            val body = DraftJson.encodeToString(entries.map { DraftEntry(it.menuId, it.variantIds, it.extras, it.note, it.quantity) })
            store.putCache(key, body, ServerClock.nowEpochSeconds())
        }
    }
}
