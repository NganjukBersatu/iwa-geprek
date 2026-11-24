package id.kongstudio.cafe.feature.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.dashboard_no_schedule
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

internal data class DashboardUiState(
    val profile: ProfileInfo? = null,
    val loading: Boolean = true,
    val attendance: AttendanceMonth? = null,
    val failure: AppFailure? = null,
    /** Penugasan hari ini; null bila belum diketahui atau jadwal ada tetapi tanpa peran. */
    val todayAssignment: UiText? = null,
    val pendingTasks: List<PendingTask> = emptyList(),
)

internal class DashboardViewModel(
    private val repository: DashboardRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(DashboardUiState())
    val state: StateFlow<DashboardUiState> = _state.asStateFlow()
    private var job: Job? = null

    fun retry() = load()

    private fun load() {
        job?.cancel()
        _state.update { it.copy(loading = true, failure = null) }
        job = viewModelScope.launch {
            if (_state.value.profile == null) {
                when (val result = repository.loadProfile()) {
                    is ApiResult.Success -> _state.update { it.copy(profile = result.value) }
                    ApiResult.Unauthorized -> return@launch onSessionExpired()
                    is ApiResult.Failure -> return@launch fail(result.failure)
                }
            }
            loadAssignment(DateTimeFormat.todayWib())
            when (val result = repository.loadAttendance()) {
                is ApiResult.Success -> _state.update { it.copy(attendance = result.value) }
                ApiResult.Unauthorized -> return@launch onSessionExpired()
                is ApiResult.Failure -> return@launch fail(result.failure)
            }
            val tasks = (repository.loadTasks() as? ApiResult.Success)?.value.orEmpty()
            val batches = (repository.loadBatches() as? ApiResult.Success)?.value.orEmpty()
            val pending = DashboardMapper.pendingTasks(tasks) + DashboardMapper.pendingBatches(batches)
            _state.update { it.copy(loading = false, pendingTasks = pending) }
        }
    }

    /** Gagal memuat jadwal tidak menggagalkan dashboard; label penugasan hanya tidak tampil. */
    private fun loadAssignment(date: String) {
        viewModelScope.launch {
            val result = repository.loadSchedule(date)
            if (result !is ApiResult.Success) return@launch
            val entries = result.value
            val label = if (entries.isEmpty()) {
                UiText.Resource(Res.string.dashboard_no_schedule)
            } else {
                entries.mapNotNull { it.roleName }.distinct().joinToString(", ")
                    .ifEmpty { null }?.let { UiText.Plain(it) }
            }
            _state.update { it.copy(todayAssignment = label) }
        }
    }

    private fun fail(failure: AppFailure) {
        _state.update { it.copy(loading = false, failure = failure) }
    }
}
