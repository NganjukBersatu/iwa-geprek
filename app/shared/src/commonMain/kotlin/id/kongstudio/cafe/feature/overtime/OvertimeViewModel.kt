package id.kongstudio.cafe.feature.overtime

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import id.kongstudio.cafe.core.text.UiText
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

internal data class OvertimeUiState(
    val entries: List<OvertimeEntry> = emptyList(),
    /** Halaman riwayat berbasis nol. */
    val page: Int = 0,
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    /** Sedang menyimpan lembur dadakan. */
    val working: Boolean = false,
    val error: UiText? = null,
) {
    val pageCount: Int get() = (entries.size + OvertimePageSize - 1) / OvertimePageSize

    val pageEntries: List<OvertimeEntry>
        get() = entries.drop(page * OvertimePageSize).take(OvertimePageSize)
}

internal class OvertimeViewModel(
    private val repository: OvertimeRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(OvertimeUiState())
    val state: StateFlow<OvertimeUiState> = _state.asStateFlow()

    fun load() {
        _state.update { it.copy(loading = it.entries.isEmpty(), failure = null) }
        viewModelScope.launch {
            when (val result = repository.history()) {
                is ApiResult.Success -> _state.update { it.copy(entries = result.value, page = 0, loading = false) }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(loading = false, failure = result.failure) }
            }
        }
    }

    fun setPage(page: Int) {
        val last = (_state.value.pageCount - 1).coerceAtLeast(0)
        _state.update { it.copy(page = page.coerceIn(0, last)) }
    }

    /** Menyimpan lembur dadakan; [onSuccess] dipanggil sebelum riwayat dimuat ulang. */
    fun record(request: OvertimeRequest, onSuccess: () -> Unit) {
        if (_state.value.working) return
        _state.update { it.copy(working = true, error = null) }
        viewModelScope.launch {
            when (val result = repository.record(request)) {
                is WriteResult.Success -> {
                    _state.update { it.copy(working = false) }
                    onSuccess()
                    load()
                }
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Failure -> _state.update { it.copy(working = false, error = UiText.Failed(result.failure)) }
            }
        }
    }

    fun clearError() = _state.update { it.copy(error = null) }
}
