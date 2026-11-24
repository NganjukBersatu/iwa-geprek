package id.kongstudio.cafe.feature.ingredientstock

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.feature.network.LiveChange
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

internal data class StockPeriodState(
    val period: OpeningPeriod? = null,
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    val asking: Boolean = false,
    val sending: Boolean = false,
    val sendFailure: AppFailure? = null,
)

/** Ringkasan periode berjalan di Stok Opname tablet dan pengajuan tutup periodenya; penutupan sendiri dilakukan admin di web. */
internal class StockPeriodViewModel(
    private val repository: IngredientStockRepository,
    private val onUnauthorized: () -> Unit,
    changes: Flow<LiveChange>?,
) : ViewModel() {
    private val _state = MutableStateFlow(StockPeriodState())
    val state: StateFlow<StockPeriodState> = _state.asStateFlow()
    private var loadJob: Job? = null

    init {
        reload()
        changes?.let { feed -> viewModelScope.launch { feed.collect { reload() } } }
    }

    fun reload() {
        loadJob?.cancel()
        _state.update { it.copy(loading = it.period == null, failure = null) }
        loadJob = viewModelScope.launch {
            when (val result = repository.openingPeriod()) {
                is DeviceResult.Ok -> _state.update { it.copy(period = result.value, loading = false) }
                is DeviceResult.Failed -> {
                    if (result.failure == AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(loading = false, failure = result.failure) }
                }
            }
        }
    }

    fun ask() = _state.update { it.copy(asking = true, sendFailure = null) }

    fun dismiss() = _state.update { if (it.sending) it else it.copy(asking = false, sendFailure = null) }

    fun send(note: String) {
        if (_state.value.sending) return
        _state.update { it.copy(sending = true, sendFailure = null) }
        viewModelScope.launch {
            when (val result = repository.requestClose(note)) {
                is DeviceResult.Ok -> {
                    _state.update { it.copy(sending = false, asking = false) }
                    reload()
                }
                is DeviceResult.Failed -> {
                    if (result.failure == AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(sending = false, sendFailure = result.failure) }
                    // Pengajuan dari tablet lain bisa sudah masuk; ringkasan dibaca ulang supaya tombolnya ikut hilang.
                    reload()
                }
            }
        }
    }
}
