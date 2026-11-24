package id.kongstudio.cafe.feature.stationboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.network.LiveFeed
import id.kongstudio.cafe.feature.printer.PaperSize
import id.kongstudio.cafe.feature.printer.PrintOutcome
import id.kongstudio.cafe.feature.printer.PrintPlan
import id.kongstudio.cafe.feature.printer.PrinterSlot
import id.kongstudio.cafe.feature.printer.ThermalPrinters
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

// Keputusan pengajuan pembatalan yang baru diterima tablet ini, ditampilkan sampai ditutup.
internal class DecisionNotice(val requestId: String, val receipt: String, val approved: Boolean, val decidedBy: String, val note: String?)

/** Struk pesanan yang belum tercetak beserta sebabnya; tetap ada sampai dicetak ulang atau ditutup. */
internal class SlipFailure(val outcome: PrintOutcome, val slips: List<StationSlip>)

/** Isi papan untuk stasiun yang terbuka: antrean kerja atau Riwayat menu yang sudah selesai. */
/** Tampilan papan satu stasiun; urutannya sama dengan urutan segmen Antrean, Proses, Selesai, Riwayat. */
internal enum class BoardView { Queue, Working, Finished, History }

/** Bagian riwayat yang dibaca server untuk tampilan ini; null untuk Antrean dan Proses yang dibaca dari papan. */
internal val BoardView.historyPart: HistoryPart?
    get() = when (this) {
        BoardView.Finished -> HistoryPart.Moving
        BoardView.History -> HistoryPart.Done
        BoardView.Queue, BoardView.Working -> null
    }

/** Riwayat satu stasiun, terbaru dulu dan berhalaman. */
internal data class HistoryState(
    val stationId: String? = null,
    val part: HistoryPart? = null,
    val loading: Boolean = false,
    val failure: AppFailure? = null,
    val entries: List<HistoryEntry> = emptyList(),
    val nextCursor: String? = null,
    val loadingMore: Boolean = false,
    val moreFailure: AppFailure? = null,
)

internal sealed interface RecipeState {
    data object Idle : RecipeState
    data object Loading : RecipeState
    class Ready(val recipe: GroupRecipe) : RecipeState
    class Failed(val failure: AppFailure) : RecipeState
}

internal data class StationBoardState(
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    val stations: List<Station> = emptyList(),
    val orders: List<BoardOrder> = emptyList(),
    // Server punya lebih banyak pesanan terbuka daripada yang terbaca sekali muat.
    val truncated: Boolean = false,
    // Tab yang sedang dibuka, salah satu stasiun yang ditetapkan untuk tablet ini.
    val activeId: String? = null,
    /** Stasiun yang bunyi menu barunya dimatikan di tablet ini. */
    val mutedIds: Set<String> = emptySet(),
    // Saluran /v2/live tersambung; selama putus, tombol dikunci karena papan bisa tertinggal.
    val connected: Boolean = false,
    // Tugas yang rinciannya sedang dibuka; kelompok diikuti lewat tugasnya karena kuncinya berubah saat tahap berganti.
    val openTaskIds: Set<String> = emptySet(),
    // Baris pesanan rincian yang terbuka, untuk memuat ulang resepnya saat berubah di web.
    val openLineIds: List<String> = emptyList(),
    val recipe: RecipeState = RecipeState.Idle,
    val stepping: Boolean = false,
    val stepFailure: AppFailure? = null,
    /** Pilihan pelaku untuk stasiun yang rinciannya dibuka; kosong sambil dimuat. */
    val workers: List<StationWorker> = emptyList(),
    val workersFailure: AppFailure? = null,
    /** Pelaku terakhir yang dipilih per stasiun; menjadi bawaan menu berikutnya sampai diganti. */
    val workerChoice: Map<String, String> = emptyMap(),
    val cancelling: Boolean = false,
    val cancelFailure: AppFailure? = null,
    val notices: List<DecisionNotice> = emptyList(),
    /** Rencana cetak tablet ini; null sampai terbaca, dan selama itu tidak ada struk stasiun yang dicetak. */
    val printPlan: PrintPlan? = null,
    val slipPrinting: Boolean = false,
    /** Struk yang gagal dicetak per stasiun, supaya peringatannya hanya tampil di tab stasiun pemiliknya. */
    val slipFailures: Map<String, SlipFailure> = emptyMap(),
    val view: BoardView = BoardView.Queue,
    val history: HistoryState = HistoryState(),
    /** Baris Riwayat yang rinciannya dibuka sebagai halaman penuh. */
    val openEntry: HistoryEntry? = null,
    val reprinting: Boolean = false,
    val reprint: ReprintResult? = null,
) {
    /** Stasiun yang ditetapkan untuk tablet ini, urut posisi stasiun; satu tab untuk tiap stasiun. */
    val held: List<Station> get() = stations.filter { it.held }
    val active: Station? get() = held.firstOrNull { it.id == activeId }

    /** Tablet ini memegang stasiun [stationId] beserta printernya: struk pesanan dicetak di sini saat Selesai dan menu baru berbunyi. */
    fun printsHere(stationId: String): Boolean = printPlan?.printsAtStation(stationId) == true
}

// Memuat papan stasiun lalu memuat ulang setiap sinyal /v2/live yang menyentuh tabelnya; tanpa polling.
internal class StationBoardViewModel(
    private val repository: StationBoardRepository,
    private val live: LiveFeed,
    private val soundPrefs: StationSoundPrefs,
    private val onUnauthorized: () -> Unit,
    private val printers: ThermalPrinters,
    printPlan: StateFlow<PrintPlan?>,
) : ViewModel() {
    private val _state = MutableStateFlow(StationBoardState())
    val state: StateFlow<StationBoardState> = _state.asStateFlow()
    private var recipeJob: Job? = null
    private var historyJob: Job? = null
    // Keputusan yang sudah ada saat papan pertama dimuat bukan kabar baru bagi tablet ini.
    private val seenDecisions = mutableSetOf<String>()
    private var firstLoad = true

    init {
        viewModelScope.launch {
            val muted = soundPrefs.muted()
            _state.update { it.copy(mutedIds = muted) }
            load()
            live.of(BoardTables).collect {
                load()
                if (_state.value.view.historyPart != null) loadHistory()
            }
        }
        viewModelScope.launch { live.connected.collect { online -> _state.update { it.copy(connected = online) } } }
        viewModelScope.launch {
            // Absen masuk atau keluar dan resep yang diubah di web mengikuti rincian yang sedang terbuka tanpa menutupnya.
            live.of(StationDetailTables).collect { reloadOpenDetail() }
        }
        viewModelScope.launch {
            // Sesi kasir baru mengembalikan semua pilihan pelaku ke bawaan, supaya pilihan hari kemarin tidak terbawa.
            live.of(CashSessionTables).collect {
                _state.update { it.copy(workerChoice = emptyMap()) }
                _state.value.activeId?.takeIf { _state.value.openTaskIds.isNotEmpty() }?.let(::loadWorkers)
                // Tanda Tertinggal dihitung server dari status sesi, jadi papan dimuat ulang saat sesi dibuka atau ditutup.
                load()
            }
        }
        // Rencana cetak dimuat dan diikuti satu pintu di kasir; papan hanya membacanya.
        viewModelScope.launch { printPlan.collect { plan -> _state.update { it.copy(printPlan = plan) } } }
    }

    /** Pindah tab; rincian yang terbuka milik tab lama ditutup. */
    fun select(stationId: String) {
        if (_state.value.held.none { it.id == stationId }) return
        _state.update {
            it.copy(activeId = stationId, openTaskIds = emptySet(), recipe = RecipeState.Idle, stepFailure = null, history = HistoryState(), openEntry = null, reprint = null)
        }
        if (_state.value.view.historyPart != null) loadHistory()
    }

    fun showView(view: BoardView) {
        if (_state.value.view == view) return
        _state.update { it.copy(view = view, openTaskIds = emptySet(), recipe = RecipeState.Idle, openEntry = null, reprint = null) }
        if (view.historyPart != null) loadHistory()
    }

    /** Halaman pertama Riwayat dibaca ulang utuh; rincian yang terbuka ikut diperbarui bila menunya masih ada. */
    private fun loadHistory() {
        val stationId = _state.value.activeId ?: return
        val part = _state.value.view.historyPart ?: return
        historyJob?.cancel()
        _state.update { current ->
            val same = current.history.stationId == stationId && current.history.part == part
            val history = if (same) current.history else HistoryState(stationId = stationId, part = part)
            current.copy(history = history.copy(loading = history.entries.isEmpty(), failure = null))
        }
        historyJob = viewModelScope.launch {
            when (val result = repository.history(stationId, part, null)) {
                is DeviceResult.Ok -> _state.update { current ->
                    if (current.activeId != stationId || current.view.historyPart != part) return@update current
                    val entries = result.value.entries
                    val open = current.openEntry?.let { opened -> entries.firstOrNull { it.taskId == opened.taskId } ?: opened }
                    current.copy(
                        history = HistoryState(stationId = stationId, part = part, entries = entries, nextCursor = result.value.nextCursor),
                        openEntry = open,
                    )
                }
                is DeviceResult.Failed -> {
                    if (result.failure is AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(history = it.history.copy(loading = false, failure = result.failure)) }
                }
            }
        }
    }

    fun retryHistory() = loadHistory()

    fun loadMoreHistory() {
        val history = _state.value.history
        val stationId = history.stationId ?: return
        val part = history.part ?: return
        val cursor = history.nextCursor ?: return
        if (history.loadingMore) return
        _state.update { it.copy(history = it.history.copy(loadingMore = true, moreFailure = null)) }
        viewModelScope.launch {
            when (val result = repository.history(stationId, part, cursor)) {
                is DeviceResult.Ok -> _state.update { current ->
                    if (current.history.stationId != stationId || current.history.part != part) return@update current
                    val known = current.history.entries.map { it.taskId }.toSet()
                    current.copy(
                        history = current.history.copy(
                            loadingMore = false,
                            entries = current.history.entries + result.value.entries.filterNot { it.taskId in known },
                            nextCursor = result.value.nextCursor,
                        ),
                    )
                }
                is DeviceResult.Failed -> {
                    if (result.failure is AppFailure.Unauthorized) onUnauthorized()
                    // Kursor yang sudah tidak berlaku ditolak server; Riwayat dibaca ulang dari awal.
                    if (result.failure is AppFailure.Rejected) {
                        _state.update { it.copy(history = it.history.copy(loadingMore = false)) }
                        loadHistory()
                    } else {
                        _state.update { it.copy(history = it.history.copy(loadingMore = false, moreFailure = result.failure)) }
                    }
                }
            }
        }
    }

    fun openHistory(entry: HistoryEntry) = _state.update { it.copy(openEntry = entry, reprint = null) }

    fun closeHistory() = _state.update { it.copy(openEntry = null, reprint = null) }

    /** Cetak ulang struk pesanan menu yang terbuka ke printer stasiun yang sedang dibuka di tablet ini. */
    fun reprintEntry() {
        val current = _state.value
        val entry = current.openEntry ?: return
        val station = current.active ?: return
        if (current.reprinting) return
        _state.update { it.copy(reprinting = true, reprint = null) }
        viewModelScope.launch {
            val slot = PrinterSlot.station(station.id)
            val paper = printers.paired.value[slot]?.paper ?: PaperSize.Mm58
            val slips = stationSlips(station, listOf(entry.order), setOf(entry.taskId), paper, ServerClock.nowEpochSeconds())
            var outcome: PrintOutcome = PrintOutcome.Ok
            for (slip in slips) {
                val printed = printers.print(slot, slip.bytes)
                if (printed != PrintOutcome.Ok) outcome = printed
            }
            val result = when {
                slips.isEmpty() -> ReprintResult.Failed
                outcome == PrintOutcome.Ok -> ReprintResult.Printed
                outcome == PrintOutcome.NotPaired -> ReprintResult.NoPrinter
                else -> ReprintResult.Failed
            }
            _state.update { it.copy(reprinting = false, reprint = result) }
        }
    }

    fun toggleSound(stationId: String) {
        val muted = _state.value.mutedIds.let { if (stationId in it) it - stationId else it + stationId }
        _state.update { it.copy(mutedIds = muted) }
        viewModelScope.launch { soundPrefs.save(muted) }
    }


    // Hanya menu yang belum pernah dicetak tablet mana pun yang dicetak di sini; struk gagal disimpan untuk dicetak ulang.
    private fun printFinished(taskIds: List<String>) {
        val current = _state.value
        val role = current.active ?: return
        if (!current.printsHere(role.id) || role.kind != StationKind.Make) return
        viewModelScope.launch {
            _state.update { it.copy(slipPrinting = true) }
            val claimed = when (val result = repository.claimPrint(taskIds)) {
                is DeviceResult.Ok -> result.value
                is DeviceResult.Failed -> {
                    if (result.failure is AppFailure.Unauthorized) onUnauthorized()
                    // Izin cetak tidak terbaca (internet putus): struk tetap dicetak supaya dapur tidak kehilangan struk.
                    taskIds.toSet()
                }
            }
            val paper = printers.paired.value[PrinterSlot.station(role.id)]?.paper ?: PaperSize.Mm58
            val slips = stationSlips(role, _state.value.orders, claimed, paper)
            sendSlips(role.id, slips)
        }
    }

    fun reprintSlips(stationId: String) {
        val failure = _state.value.slipFailures[stationId] ?: return
        if (_state.value.slipPrinting) return
        viewModelScope.launch {
            _state.update { it.copy(slipPrinting = true, slipFailures = it.slipFailures - stationId) }
            sendSlips(stationId, failure.slips)
        }
    }

    private suspend fun sendSlips(stationId: String, slips: List<StationSlip>) {
        val failed = mutableListOf<StationSlip>()
        var outcome: PrintOutcome = PrintOutcome.Interrupted
        for (slip in slips) {
            // Printer stasiun yang terputus tidak dialihkan ke printer lain; struknya disimpan untuk dicetak ulang.
            val result = printers.print(PrinterSlot.station(stationId), slip.bytes)
            if (result != PrintOutcome.Ok) {
                failed += slip
                outcome = result
            }
        }
        _state.update { current ->
            val earlier = current.slipFailures[stationId]
            val failures = if (failed.isEmpty()) current.slipFailures else current.slipFailures + (stationId to SlipFailure(outcome, earlier?.slips.orEmpty() + failed))
            current.copy(slipPrinting = false, slipFailures = failures)
        }
    }

    fun reload() {
        _state.update { it.copy(loading = true, failure = null) }
        viewModelScope.launch { load() }
    }

    fun open(group: QueueGroup) {
        _state.update { it.copy(openTaskIds = group.taskIds.toSet(), openLineIds = group.portions.mapNotNull { it.line.id }, stepFailure = null, recipe = RecipeState.Idle) }
        val role = _state.value.active
        val lineIds = group.portions.mapNotNull { it.line.id }
        if (role?.kind == StationKind.Make && lineIds.isNotEmpty()) loadRecipe(lineIds)
        if (role != null && role.kind != StationKind.Handover) loadWorkers(role.id)
    }

    // Daftar dimuat tiap rincian dibuka, karena yang absen masuk atau keluar berubah sepanjang hari.
    private fun loadWorkers(stationId: String) {
        viewModelScope.launch {
            when (val result = repository.workers(stationId)) {
                is DeviceResult.Ok -> _state.update { current ->
                    val choice = current.workerChoice[stationId]
                    // Pilihan yang tidak lagi memenuhi syarat (misalnya sudah absen keluar) kembali ke bawaan.
                    val stillValid = choice == null || result.value.any { it.userId == choice }
                    current.copy(
                        workers = result.value,
                        workersFailure = null,
                        workerChoice = if (stillValid) current.workerChoice else current.workerChoice - stationId,
                    )
                }
                is DeviceResult.Failed -> {
                    if (result.failure is AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(workers = emptyList(), workersFailure = result.failure) }
                }
            }
        }
    }

    private fun reloadOpenDetail() {
        val current = _state.value
        if (current.openTaskIds.isEmpty()) return
        val role = current.active ?: return
        if (role.kind != StationKind.Handover) loadWorkers(role.id)
        if (role.kind == StationKind.Make) {
            val lineIds = current.openLineIds
            if (lineIds.isNotEmpty()) loadRecipe(lineIds)
        }
    }

    fun chooseWorker(stationId: String, userId: String) =
        _state.update { it.copy(workerChoice = it.workerChoice + (stationId to userId)) }

    fun close() = _state.update { it.copy(openTaskIds = emptySet(), openLineIds = emptyList(), recipe = RecipeState.Idle, stepFailure = null) }

    private fun loadRecipe(lineIds: List<String>) {
        recipeJob?.cancel()
        _state.update { it.copy(recipe = RecipeState.Loading) }
        recipeJob = viewModelScope.launch {
            when (val result = repository.recipe(lineIds)) {
                is DeviceResult.Ok -> _state.update { it.copy(recipe = RecipeState.Ready(result.value)) }
                is DeviceResult.Failed -> {
                    if (result.failure is AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(recipe = RecipeState.Failed(result.failure)) }
                }
            }
        }
    }

    // Satu langkah untuk tugas terpilih; yang sudah selesai keluar dari rincian yang terbuka.
    fun step(step: StepKind, taskIds: List<String>, seen: Stage) {
        if (_state.value.stepping || taskIds.isEmpty()) return
        _state.update { it.copy(stepping = true, stepFailure = null) }
        viewModelScope.launch {
            val workerId = _state.value.activeId?.let { _state.value.workerChoice[it] }
            when (val result = repository.step(step, taskIds, seen, workerId)) {
                is DeviceResult.Ok -> {
                    _state.update { current ->
                        var orders = current.orders
                        result.value.forEach { orders = orders.upsert(it) }
                        current.copy(stepping = false, orders = orders, openTaskIds = current.openTaskIds.stillOpen(orders, current.activeId))
                    }
                    if (step == StepKind.Finish) printFinished(taskIds)
                }
                is DeviceResult.Failed -> {
                    if (result.failure is AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(stepping = false, stepFailure = result.failure) }
                    // Ditolak karena basi (tablet lain lebih dulu): ambil keadaan terkini.
                    if (result.failure is AppFailure.Rejected || result.failure is AppFailure.NotFound) {
                        load()
                        _state.value.activeId?.let(::loadWorkers)
                    }
                }
            }
        }
    }

    fun dismissStepFailure() = _state.update { it.copy(stepFailure = null) }

    fun withdrawCancel(requestId: String) = cancelAction { repository.withdrawCancel(requestId) }

    fun dismissNotice(requestId: String) = _state.update { state -> state.copy(notices = state.notices.filterNot { it.requestId == requestId }) }

    private fun cancelAction(call: suspend () -> DeviceResult<Unit>) {
        if (_state.value.cancelling) return
        _state.update { it.copy(cancelling = true, cancelFailure = null) }
        viewModelScope.launch {
            when (val result = call()) {
                is DeviceResult.Ok -> {
                    _state.update { it.copy(cancelling = false) }
                    load()
                }
                is DeviceResult.Failed -> {
                    if (result.failure is AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(cancelling = false, cancelFailure = result.failure) }
                }
            }
        }
    }

    // Keadaan penuh setiap kali; keputusan pembatalan yang baru masuk dijadikan pemberitahuan.
    private suspend fun load() {
        when (val stations = repository.stations()) {
            is DeviceResult.Failed -> return fail(stations.failure)
            is DeviceResult.Ok -> _state.update { current ->
                val held = stations.value.filter { it.held }
                // Tab terakhir tetap dibuka bila masih ditetapkan; selain itu tab pertama.
                val active = current.activeId?.takeIf { id -> held.any { it.id == id } } ?: held.firstOrNull()?.id
                current.copy(stations = stations.value, activeId = active)
            }
        }
        when (val board = repository.board()) {
            is DeviceResult.Failed -> fail(board.failure)
            is DeviceResult.Ok -> {
                val fresh = board.value.orders.mapNotNull { order ->
                    val decision = order.decision ?: return@mapNotNull null
                    if (!seenDecisions.add(decision.id) || firstLoad) return@mapNotNull null
                    DecisionNotice(decision.id, order.receipt, decision.approved, decision.decidedBy, decision.note)
                }
                firstLoad = false
                _state.update { current ->
                    current.copy(
                        orders = board.value.orders,
                        truncated = board.value.truncated,
                        loading = false,
                        failure = null,
                        notices = current.notices + fresh,
                        openTaskIds = current.openTaskIds.stillOpen(board.value.orders, current.activeId),
                    )
                }
            }
        }
    }

    private fun fail(failure: AppFailure) {
        if (failure is AppFailure.Unauthorized) onUnauthorized()
        _state.update { it.copy(loading = false, failure = failure) }
    }
}

// Rincian tetap terbuka selama masih ada tugasnya yang belum selesai di stasiun ini.
private fun Set<String>.stillOpen(orders: List<BoardOrder>, stationId: String?): Set<String> {
    if (isEmpty() || stationId == null) return emptySet()
    val live = orders.asSequence()
        .filter { !it.voided }
        .flatMap { it.lines.asSequence() }
        .mapNotNull { it.taskAt(stationId) }
        .filter { it.id in this && !it.removed && it.stage != Stage.Finished }
        .map { it.id }
        .toSet()
    return live
}

private fun List<BoardOrder>.upsert(order: BoardOrder): List<BoardOrder> {
    val index = indexOfFirst { it.id == order.id }
    return if (index < 0) (this + order).sortedBy { it.createdEpoch } else toMutableList().also { it[index] = order }
}
