package id.kongstudio.cafe.feature.attendancelog

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.format.YearMonth
import id.kongstudio.cafe.core.network.ApiResult
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

internal data class AttendanceLogUiState(
    val month: YearMonth? = null,
    val attendance: AttendanceMonth? = null,
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    val canGoNext: Boolean = false,
)

internal class AttendanceLogViewModel(
    private val repository: AttendanceLogRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(AttendanceLogUiState())
    val state: StateFlow<AttendanceLogUiState> = _state.asStateFlow()

    /** Bulan berjalan menurut server, diketahui dari pemuatan pertama tanpa parameter. */
    private var currentMonth: YearMonth? = null
    private var job: Job? = null

    fun retry() = load(_state.value.month)

    fun previousMonth() {
        _state.value.month?.let { load(it.previous()) }
    }

    fun nextMonth() {
        val month = _state.value.month ?: return
        if (_state.value.canGoNext) load(month.next())
    }

    private fun load(target: YearMonth?) {
        job?.cancel()
        _state.update { it.copy(loading = true, failure = null, month = target ?: it.month) }
        job = viewModelScope.launch {
            when (val result = repository.load(target)) {
                is ApiResult.Success -> {
                    val month = result.value.month
                    if (target == null) currentMonth = month
                    _state.update {
                        it.copy(attendance = result.value, month = month, loading = false, canGoNext = month != currentMonth)
                    }
                }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(loading = false, failure = result.failure) }
            }
        }
    }
}
