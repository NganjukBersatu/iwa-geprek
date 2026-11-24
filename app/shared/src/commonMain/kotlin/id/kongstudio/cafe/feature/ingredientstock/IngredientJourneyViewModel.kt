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

internal data class JourneyState(
    val journey: StockJourney? = null,
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    val saving: Boolean = false,
    val saveFailure: AppFailure? = null,
)

/** Stok awal dan perjalanan stok satu bahan di periode berjalan, beserta isi, ubah, dan hapus stok awalnya. */
internal class IngredientJourneyViewModel(
    private val ingredientId: String,
    private val repository: IngredientStockRepository,
    private val onUnauthorized: () -> Unit,
    changes: Flow<LiveChange>?,
) : ViewModel() {
    private val _state = MutableStateFlow(JourneyState())
    val state: StateFlow<JourneyState> = _state.asStateFlow()
    private var loadJob: Job? = null

    init {
        reload()
        changes?.let { feed -> viewModelScope.launch { feed.collect { reload() } } }
    }

    fun reload() {
        loadJob?.cancel()
        _state.update { it.copy(loading = it.journey == null, failure = null) }
        loadJob = viewModelScope.launch {
            when (val result = repository.journey(ingredientId)) {
                is DeviceResult.Ok -> _state.update { it.copy(journey = result.value, loading = false) }
                is DeviceResult.Failed -> {
                    if (result.failure == AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(loading = false, failure = result.failure) }
                }
            }
        }
    }

    fun clearSaveFailure() = _state.update { it.copy(saveFailure = null) }

    /** [qty] sudah dirapikan lewat StockQuantity.parse. */
    fun setOpening(qty: String, onDone: () -> Unit) = save(onDone) { repository.setOpening(ingredientId, qty) }

    fun removeOpening(onDone: () -> Unit) = save(onDone) { repository.removeOpening(ingredientId) }

    private fun save(onDone: () -> Unit, request: suspend () -> DeviceResult<StockJourney>) {
        if (_state.value.saving) return
        _state.update { it.copy(saving = true, saveFailure = null) }
        viewModelScope.launch {
            when (val result = request()) {
                is DeviceResult.Ok -> {
                    _state.update { it.copy(saving = false, journey = result.value) }
                    onDone()
                }
                is DeviceResult.Failed -> {
                    if (result.failure == AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(saving = false, saveFailure = result.failure) }
                }
            }
        }
    }
}
