package id.kongstudio.cafe.feature.stationboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.feature.cashier.PrintReport
import id.kongstudio.cafe.feature.cashier.PrintableOrder
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.network.LiveFeed
import id.kongstudio.cafe.feature.printer.PrintPlan
import id.kongstudio.cafe.feature.printer.PrinterSlot
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

private const val SearchDebounceMillis = 250L

internal enum class ReprintResult { Printed, NoPrinter, Failed }

/** Hasil cetak ulang terakhir untuk printer [slot]. */
internal class ReprintStatus(val slot: PrinterSlot, val result: ReprintResult)

/** Cetak ulang pesanan lama lewat kasir: rencana cetak dan antrean cetak milik kasir. */
internal class OrderReprinter(
    val categoryOf: (String?) -> String?,
    val slots: (PrintableOrder) -> List<PrinterSlot>,
    val print: suspend (PrintableOrder, PrinterSlot) -> PrintReport,
    val plan: () -> PrintPlan?,
)

internal data class CashierOrdersState(
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    val query: String = "",
    val orders: List<CashierOrder> = emptyList(),
    /** Pesanan tertinggal dari sesi lain yang sudah ditutup; tampil di atas daftar selama tidak mencari. */
    val leftBehind: List<CashierOrder> = emptyList(),
    /** Daftar tertinggal gagal dibaca; daftar terakhir tetap dipakai dan daftar sesi ini tidak ikut gagal. */
    val leftBehindFailure: AppFailure? = null,
    val nextCursor: String? = null,
    val loadingMore: Boolean = false,
    val moreFailure: AppFailure? = null,
    // Rincian yang terbuka disimpan utuh, supaya tetap tampil walau muat ulang hanya membaca halaman pertama.
    val openOrder: CashierOrder? = null,
    val askingCancel: Boolean = false,
    val cancelling: Boolean = false,
    val cancelFailure: AppFailure? = null,
    /** Printer yang sedang mencetak ulang; null bila tidak ada. */
    val printing: PrinterSlot? = null,
    val reprint: ReprintStatus? = null,
)

// Pesanan sesi aktif untuk station Kasir; dimuat ulang setiap sinyal /v2/live yang menyentuh pesanan, tanpa polling.
internal class CashierOrdersViewModel(
    private val sessionId: String,
    private val repository: CashierOrderRepository,
    private val board: StationBoardRepository,
    live: LiveFeed,
    private val reprinter: OrderReprinter,
    private val onUnauthorized: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(CashierOrdersState())
    val state: StateFlow<CashierOrdersState> = _state.asStateFlow()
    private var firstPageJob: Job? = null

    init {
        loadFirstPage(debounce = false)
        viewModelScope.launch { live.of(BoardTables).collect { loadFirstPage(debounce = false) } }
    }

    fun search(query: String) {
        _state.update { it.copy(query = query) }
        loadFirstPage(debounce = true)
    }

    fun retry() {
        _state.update { it.copy(loading = true, failure = null) }
        loadFirstPage(debounce = false)
    }

    // Halaman pertama selalu dibaca ulang utuh; halaman yang sudah dimuat ikut diganti supaya status tidak basi.
    private fun loadFirstPage(debounce: Boolean) {
        firstPageJob?.cancel()
        firstPageJob = viewModelScope.launch {
            if (debounce) delay(SearchDebounceMillis)
            val query = _state.value.query
            when (val found = repository.leftBehind(sessionId)) {
                is DeviceResult.Ok -> _state.update { it.copy(leftBehind = found.value, leftBehindFailure = null) }
                is DeviceResult.Failed -> _state.update { it.copy(leftBehindFailure = found.failure) }
            }
            when (val result = repository.page(sessionId, query, null)) {
                is DeviceResult.Ok -> _state.update {
                    val fresh = result.value.orders
                    val known = fresh + it.leftBehind
                    val open = it.openOrder?.let { opened -> known.firstOrNull { order -> order.id == opened.id } ?: opened }
                    it.copy(loading = false, failure = null, orders = fresh, nextCursor = result.value.nextCursor, moreFailure = null, openOrder = open)
                }
                is DeviceResult.Failed -> {
                    if (result.failure is AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(loading = false, failure = result.failure) }
                }
            }
        }
    }

    fun loadMore() {
        val current = _state.value
        val cursor = current.nextCursor ?: return
        if (current.loadingMore) return
        _state.update { it.copy(loadingMore = true, moreFailure = null) }
        viewModelScope.launch {
            when (val result = repository.page(sessionId, current.query, cursor)) {
                is DeviceResult.Ok -> _state.update { state ->
                    val known = state.orders.map { it.id }.toSet()
                    state.copy(loadingMore = false, orders = state.orders + result.value.orders.filterNot { it.id in known }, nextCursor = result.value.nextCursor)
                }
                is DeviceResult.Failed -> {
                    if (result.failure is AppFailure.Unauthorized) onUnauthorized()
                    // Kursor yang sudah tidak berlaku ditolak server; daftar dibaca ulang dari awal.
                    if (result.failure is AppFailure.Rejected) {
                        _state.update { it.copy(loadingMore = false) }
                        loadFirstPage(debounce = false)
                    } else {
                        _state.update { it.copy(loadingMore = false, moreFailure = result.failure) }
                    }
                }
            }
        }
    }

    fun open(order: CashierOrder) = _state.update { it.copy(openOrder = order, reprint = null, cancelFailure = null) }

    fun close() = _state.update { it.copy(openOrder = null, askingCancel = false, reprint = null, cancelFailure = null) }

    /** Struk yang bisa dicetak ulang untuk pesanan yang terbuka: pembayaran, dan stasiun tanpa tablet yang punya menunya. */
    fun reprintSlots(order: CashierOrder): List<PrinterSlot> = reprinter.slots(order.toPrintable(reprinter.categoryOf))

    /** Rencana cetak saat ini, untuk menamai printer stasiun di tombol dan pesan. */
    fun printPlan(): PrintPlan? = reprinter.plan()

    fun reprint(slot: PrinterSlot) {
        val order = _state.value.openOrder ?: return
        if (_state.value.printing != null) return
        _state.update { it.copy(printing = slot, reprint = null) }
        viewModelScope.launch {
            val report = reprinter.print(order.toPrintable(reprinter.categoryOf, ServerClock.nowEpochSeconds()), slot)
            val result = when {
                report.ok && report.printedAny -> ReprintResult.Printed
                report.failed.isEmpty() -> ReprintResult.NoPrinter
                else -> ReprintResult.Failed
            }
            _state.update { it.copy(printing = null, reprint = ReprintStatus(slot, result)) }
        }
    }

    fun askCancel() = _state.update { it.copy(askingCancel = true, cancelFailure = null) }

    fun closeCancel() = _state.update { it.copy(askingCancel = false, cancelFailure = null) }

    fun requestCancel(reason: String) {
        val order = _state.value.openOrder ?: return
        cancelAction { board.requestCancel(order.id, reason) }
    }

    fun withdrawCancel() {
        val request = _state.value.openOrder?.pendingCancel ?: return
        cancelAction { board.withdrawCancel(request.id) }
    }

    private fun cancelAction(call: suspend () -> DeviceResult<Unit>) {
        if (_state.value.cancelling) return
        _state.update { it.copy(cancelling = true, cancelFailure = null) }
        viewModelScope.launch {
            when (val result = call()) {
                is DeviceResult.Ok -> {
                    _state.update { it.copy(cancelling = false, askingCancel = false) }
                    loadFirstPage(debounce = false)
                }
                is DeviceResult.Failed -> {
                    if (result.failure is AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(cancelling = false, cancelFailure = result.failure) }
                }
            }
        }
    }
}
