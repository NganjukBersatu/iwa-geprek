package id.kongstudio.cafe.feature.ordersync

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.feature.network.LiveFeed
import id.kongstudio.cafe.offline.OfflineStore
import id.kongstudio.cafe.offline.QueueCounts
import id.kongstudio.cafe.offline.QueueStatus
import id.kongstudio.cafe.offline.QueuedOrder
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Hasil satu Kirim sekarang: berapa terkirim, berapa ditolak, dan berapa masih menunggu karena server tidak terjangkau. */
internal class SyncReport(val sent: Int, val rejected: Int, val waiting: Int)

internal data class OrderSyncState(
    val counts: QueueCounts = QueueCounts(),
    val rejected: List<QueuedOrder> = emptyList(),
    /** Seluruh antrean tablet, terlama dulu; halaman Mode Offline menampilkannya per pesanan. */
    val orders: List<QueuedOrder> = emptyList(),
    /** Lembar pesanan ditolak sedang terbuka; dibuka dari banner atau dari gerbang tutup sesi. */
    val reviewing: Boolean = false,
    /** Antrean sedang dikirim, otomatis atau dari tombol. */
    val sending: Boolean = false,
    /** Hasil Kirim sekarang terakhir; hilang saat dikirim lagi. */
    val report: SyncReport? = null,
    /** Saluran /v2/live tersambung, dipakai sebagai tanda server terjangkau. */
    val online: Boolean = false,
)

/**
 * Menjaga antrean pesanan tablet: mengirim saat ada antrean baru atau server terjangkau lagi, dan memberi karyawan jalan atas
 * pesanan yang ditolak. [ownerId] karyawan pemegang tablet; hanya antreannya yang bisa dikirim dengan tokennya.
 */
internal class OrderSyncViewModel(
    private val syncer: OrderSyncer,
    private val store: OfflineStore,
    live: LiveFeed,
    val ownerId: String?,
    private val onLoginRequired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(OrderSyncState())
    val state: StateFlow<OrderSyncState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            store.counts().collect { counts ->
                val rejected = if (counts.rejected > 0) store.rejected() else emptyList()
                _state.update { it.copy(counts = counts, rejected = rejected) }
            }
        }
        viewModelScope.launch { store.all().collect { orders -> _state.update { it.copy(orders = orders) } } }
        viewModelScope.launch {
            store.counts().map { it.queued }.distinctUntilChanged().filter { it > 0 }.collect { flush() }
        }
        viewModelScope.launch {
            live.connected.collect { online ->
                _state.update { it.copy(online = online) }
                if (online) flush()
            }
        }
    }

    /** Pesanan milik karyawan ini yang masih menunggu; yang tertahan menunggu masuk ulang juga ikut dicoba dengan token sekarang. */
    private fun ownWaiting(orders: List<QueuedOrder>): Int =
        orders.count { it.userId == ownerId && it.status != QueueStatus.Rejected }

    private fun ownRejected(orders: List<QueuedOrder>): Int =
        orders.count { it.userId == ownerId && it.status == QueueStatus.Rejected }

    fun syncNow() {
        if (_state.value.sending) return
        _state.update { it.copy(report = null) }
        viewModelScope.launch {
            val before = _state.value.orders
            val outcome = flush()
            if (outcome == FlushOutcome.LoginRequired) return@launch
            val after = store.all().first()
            val rejected = (ownRejected(after) - ownRejected(before)).coerceAtLeast(0)
            val waiting = ownWaiting(after)
            val sent = (ownWaiting(before) - waiting - rejected).coerceAtLeast(0)
            _state.update { it.copy(report = SyncReport(sent, rejected, waiting)) }
        }
    }

    fun openReview() = _state.update { it.copy(reviewing = true) }

    fun closeReview() = _state.update { it.copy(reviewing = false) }

    fun clearReport() = _state.update { it.copy(report = null) }

    /** Mengembalikan pesanan yang ditolak ke antrean, setelah penyebabnya dibereskan karyawan. */
    fun retry(clientId: String) {
        viewModelScope.launch {
            store.requeue(clientId)
            flush()
        }
    }

    /** Membuang pesanan yang ditolak atas keputusan karyawan; satu-satunya jalan pesanan dihapus tanpa dikirim. */
    fun discard(clientId: String) {
        viewModelScope.launch { store.delete(clientId) }
    }

    private suspend fun flush(): FlushOutcome {
        _state.update { it.copy(sending = true) }
        val outcome = try {
            syncer.flush()
        } finally {
            _state.update { it.copy(sending = false) }
        }
        if (outcome == FlushOutcome.LoginRequired) onLoginRequired()
        return outcome
    }
}
