package id.kongstudio.cafe.feature.attendance.selfschedule

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import id.kongstudio.cafe.core.text.UiText
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Langkah absen mandiri: pemberitahuan tidak terdaftar, lalu isian jadwal. */
internal enum class SelfScheduleStep { Intro, Form }

internal data class SelfScheduleUiState(
    val step: SelfScheduleStep? = null,
    val options: SelfScheduleOptions? = null,
    val loading: Boolean = false,
    val outletId: String? = null,
    val roleId: String? = null,
    val shiftCodeId: String? = null,
    val reason: String = "",
    val submitting: Boolean = false,
    val error: UiText? = null,
) {
    val canSubmit: Boolean get() = outletId != null && roleId != null && shiftCodeId != null && !loading
}

internal class SelfScheduleViewModel(
    private val repository: SelfScheduleRepository,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(SelfScheduleUiState())
    val state: StateFlow<SelfScheduleUiState> = _state.asStateFlow()
    private var job: Job? = null

    fun start() = _state.update { SelfScheduleUiState(step = SelfScheduleStep.Intro) }

    fun close() {
        job?.cancel()
        _state.value = SelfScheduleUiState()
    }

    /** Membuka isian dan memuat cabang serta peran. */
    fun openForm() {
        _state.update { it.copy(step = SelfScheduleStep.Form) }
        load(null)
    }

    /** Ganti cabang mengosongkan kode shift karena saran kode milik cabang. */
    fun selectOutlet(outletId: String?) {
        if (outletId == _state.value.outletId) return
        _state.update { it.copy(outletId = outletId, shiftCodeId = null, error = null) }
        load(outletId)
    }

    fun selectRole(roleId: String?) = _state.update { it.copy(roleId = roleId, error = null) }

    fun selectShift(shiftCodeId: String) = _state.update { it.copy(shiftCodeId = shiftCodeId, error = null) }

    fun changeReason(reason: String) = _state.update { it.copy(reason = reason) }

    /** Menyimpan jadwal; [onCreated] menerima id jadwal baru untuk absen datang. */
    fun submit(onCreated: (scheduleId: String) -> Unit) {
        val current = _state.value
        if (current.submitting || !current.canSubmit) return
        val request = SelfScheduleRequest(
            outletId = current.outletId ?: return,
            roleId = current.roleId ?: return,
            shiftCodeId = current.shiftCodeId ?: return,
            reason = current.reason.trim().ifEmpty { null },
        )
        _state.update { it.copy(submitting = true, error = null) }
        viewModelScope.launch {
            when (val result = repository.create(request)) {
                is WriteResult.Success -> {
                    _state.value = SelfScheduleUiState()
                    onCreated(result.value)
                }
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Failure -> _state.update { it.copy(submitting = false, error = UiText.Failed(result.failure)) }
            }
        }
    }

    private fun load(outletId: String?) {
        job?.cancel()
        _state.update { it.copy(loading = true, error = null) }
        job = viewModelScope.launch {
            when (val result = repository.options(outletId)) {
                is ApiResult.Success -> _state.update { it.copy(options = result.value, loading = false) }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(loading = false, error = UiText.Failed(result.failure)) }
            }
        }
    }
}
