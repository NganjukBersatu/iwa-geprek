package id.kongstudio.cafe.feature.sop

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Tanda selesai membaca yang belum diterima server, disimpan untuk dikirim ulang. */
internal class PendingRead(val sopId: String, val version: Int)

internal data class SopUiState(
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    val items: List<SopSummary> = emptyList(),
    /** Versi tiap SOP yang sudah diselesaikan sampai slide terakhir, dari server. */
    val read: Map<String, Int> = emptyMap(),
    val opening: Boolean = false,
    val openFailure: AppFailure? = null,
    val opened: SopDocument? = null,
    val pendingRead: PendingRead? = null,
    val markFailure: AppFailure? = null,
) {
    fun isNew(item: SopSummary) = (read[item.id] ?: 0) < item.version
}

internal class SopViewModel(
    private val repository: SopRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(SopUiState())
    val state: StateFlow<SopUiState> = _state.asStateFlow()
    private var job: Job? = null

    init {
        load()
    }

    fun load() {
        job?.cancel()
        _state.update { it.copy(loading = true, failure = null) }
        job = viewModelScope.launch {
            val items = async { repository.list() }
            val reads = async { repository.reads() }
            val listed = items.await()
            val marked = reads.await()
            when {
                listed is ApiResult.Unauthorized || marked is ApiResult.Unauthorized -> onSessionExpired()
                listed is ApiResult.Failure -> _state.update { it.copy(loading = false, failure = listed.failure) }
                marked is ApiResult.Failure -> _state.update { it.copy(loading = false, failure = marked.failure) }
                listed is ApiResult.Success && marked is ApiResult.Success ->
                    _state.update { it.copy(items = listed.value, read = marked.value, loading = false) }
            }
        }
    }

    fun open(item: SopSummary) {
        if (_state.value.opening) return
        _state.update { it.copy(opening = true, openFailure = null) }
        viewModelScope.launch {
            when (val result = repository.load(item.id)) {
                is ApiResult.Success -> _state.update { it.copy(opening = false, opened = result.value) }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(opening = false, openFailure = result.failure) }
            }
        }
    }

    /** Keluar sebelum slide terakhir tidak dihitung membaca. */
    fun close() = _state.update { it.copy(opened = null) }

    /** Slide terakhir selesai: tanda Baru langsung hilang, lalu tandanya dikirim ke server. */
    fun finish() {
        val document = _state.value.opened ?: return
        val pending = PendingRead(document.id, document.version)
        _state.update { current ->
            val known = current.read[document.id] ?: 0
            current.copy(opened = null, read = current.read + (document.id to maxOf(known, document.version)))
        }
        send(pending)
    }

    fun retryRead() {
        _state.value.pendingRead?.let(::send)
    }

    private fun send(pending: PendingRead) {
        _state.update { it.copy(pendingRead = pending, markFailure = null) }
        viewModelScope.launch {
            when (val result = repository.markRead(pending.sopId, pending.version)) {
                is WriteResult.Success -> _state.update { it.copy(pendingRead = null) }
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Failure -> _state.update { it.copy(markFailure = result.failure) }
            }
        }
    }
}
