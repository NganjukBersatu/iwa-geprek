package id.kongstudio.cafe.feature.performance

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.network.ApiResult
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

internal data class PerformanceUiState(
    val range: PerformanceRange = PerformanceRange.Cycle,
    val performance: Performance? = null,
    val loading: Boolean = true,
    val failure: AppFailure? = null,
)

internal class PerformanceViewModel(
    private val repository: PerformanceRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(PerformanceUiState())
    val state: StateFlow<PerformanceUiState> = _state.asStateFlow()
    private var job: Job? = null

    fun select(range: PerformanceRange) {
        if (range != _state.value.range) load(range)
    }

    fun retry() = load(_state.value.range)

    private fun load(range: PerformanceRange) {
        job?.cancel()
        _state.update { it.copy(range = range, loading = true, failure = null) }
        job = viewModelScope.launch {
            when (val result = repository.load(range)) {
                is ApiResult.Success -> _state.update { it.copy(performance = result.value, loading = false) }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(loading = false, failure = result.failure) }
            }
        }
    }
}
