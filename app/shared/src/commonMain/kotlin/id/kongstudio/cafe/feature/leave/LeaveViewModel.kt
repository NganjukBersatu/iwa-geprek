package id.kongstudio.cafe.feature.leave

import id.kongstudio.cafe.core.failure.AppFailure
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.resources.Res
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

internal data class LeaveUiState(
    val items: List<LeaveRequest> = emptyList(),
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    /** Sedang mengirim atau membatalkan pengajuan. */
    val working: Boolean = false,
    val error: UiText? = null,
)

internal class LeaveViewModel(
    private val repository: LeaveRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(LeaveUiState())
    val state: StateFlow<LeaveUiState> = _state.asStateFlow()

    fun load() {
        _state.update { it.copy(loading = it.items.isEmpty(), failure = null) }
        viewModelScope.launch {
            when (val result = repository.load()) {
                is ApiResult.Success -> _state.update { it.copy(items = result.value, loading = false) }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(loading = false, failure = result.failure) }
            }
        }
    }

    fun submit(form: LeaveForm, attachment: LeaveAttachment?, onSuccess: () -> Unit) =
        run(onSuccess) { repository.submit(form, attachment) }

    fun cancel(id: String, onSuccess: () -> Unit) = run(onSuccess) { repository.cancel(id) }

    fun clearError() = _state.update { it.copy(error = null) }

    private fun run(onSuccess: () -> Unit, send: suspend () -> WriteResult<Unit>) {
        if (_state.value.working) return
        _state.update { it.copy(working = true, error = null) }
        viewModelScope.launch {
            when (val result = send()) {
                is WriteResult.Success -> {
                    _state.update { it.copy(working = false) }
                    onSuccess()
                    load()
                }
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Failure -> fail(UiText.Failed(result.failure))
            }
        }
    }

    private fun fail(text: UiText) {
        _state.update { it.copy(working = false, error = text) }
    }
}
