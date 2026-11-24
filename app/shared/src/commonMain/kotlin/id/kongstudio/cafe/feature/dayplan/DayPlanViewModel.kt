package id.kongstudio.cafe.feature.dayplan

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

internal data class DayPlanUiState(
    val plan: DayPlan? = null,
    val failure: AppFailure? = null,
)

internal class DayPlanViewModel(
    private val repository: DayPlanRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(DayPlanUiState())
    val state: StateFlow<DayPlanUiState> = _state.asStateFlow()
    private var job: Job? = null

    /** Dipanggil tiap halaman dibuka dan setelah lembur dadakan tersimpan. */
    fun load() {
        job?.cancel()
        job = viewModelScope.launch {
            when (val result = repository.load()) {
                is ApiResult.Success -> _state.update { DayPlanUiState(plan = result.value) }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(failure = result.failure) }
            }
        }
    }
}
