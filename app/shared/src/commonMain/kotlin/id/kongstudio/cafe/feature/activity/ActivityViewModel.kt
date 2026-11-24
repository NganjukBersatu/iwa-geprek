package id.kongstudio.cafe.feature.activity

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

internal const val ActivityPageSize = 10

internal data class ActivityUiState(
    val group: ActivityGroup = ActivityGroup.All,
    val events: List<ActivityEvent> = emptyList(),
    /** Halaman daftar, berbasis nol. */
    val page: Int = 0,
    val loading: Boolean = true,
    val failure: AppFailure? = null,
) {
    val pageCount: Int
        get() = (events.size + ActivityPageSize - 1) / ActivityPageSize
}

internal class ActivityViewModel(
    private val repository: ActivityRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(ActivityUiState())
    val state: StateFlow<ActivityUiState> = _state.asStateFlow()
    private var job: Job? = null

    init {
        load(ActivityGroup.All)
    }

    fun select(group: ActivityGroup) {
        if (group != _state.value.group) load(group)
    }

    fun retry() = load(_state.value.group)

    fun setPage(page: Int) {
        _state.update { it.copy(page = page.coerceIn(0, (it.pageCount - 1).coerceAtLeast(0))) }
    }

    private fun load(group: ActivityGroup) {
        job?.cancel()
        _state.update { it.copy(group = group, events = emptyList(), page = 0, loading = true, failure = null) }
        job = viewModelScope.launch {
            when (val result = repository.load(group)) {
                is ApiResult.Success -> _state.update { it.copy(events = result.value, loading = false) }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(loading = false, failure = result.failure) }
            }
        }
    }
}
