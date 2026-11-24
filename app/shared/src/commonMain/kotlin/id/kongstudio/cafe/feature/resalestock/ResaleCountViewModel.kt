package id.kongstudio.cafe.feature.resalestock

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.format.StockQuantity
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

internal enum class ResaleCountProblem { None, NoLines, Invalid }

internal data class ResaleCountState(
    val counting: Boolean = false,
    val typed: Map<String, String> = emptyMap(),
    val note: String = "",
    val problem: ResaleCountProblem = ResaleCountProblem.None,
    val confirming: Boolean = false,
    val closing: Boolean = false,
    val closeFailure: AppFailure? = null,
    val result: ResaleCountResult? = null,
) {
    val filled: Int get() = typed.values.count { it.isNotBlank() }
}

/** Isian jumlah fisik satu opname di tablet; stok sistem dibaca dan disamakan oleh server saat disimpan. */
internal class ResaleCountViewModel(
    private val repository: ResaleStockRepository,
    private val onUnauthorized: () -> Unit,
    private val onSaved: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(ResaleCountState())
    val state: StateFlow<ResaleCountState> = _state.asStateFlow()

    fun start() = _state.update { ResaleCountState(counting = true) }

    fun cancel() = _state.update { ResaleCountState() }

    fun type(menuItemId: String, text: String) =
        _state.update { it.copy(typed = it.typed + (menuItemId to text), problem = ResaleCountProblem.None, result = null) }

    fun setNote(text: String) = _state.update { it.copy(note = text) }

    /** Memeriksa isian lebih dulu; konfirmasi hanya muncul bila ada yang bisa disimpan. */
    fun askClose() {
        val parsed = parsedLines()
        val problem = when {
            parsed == null -> ResaleCountProblem.Invalid
            parsed.isEmpty() -> ResaleCountProblem.NoLines
            else -> ResaleCountProblem.None
        }
        _state.update { it.copy(problem = problem, confirming = problem == ResaleCountProblem.None, closeFailure = null) }
    }

    fun dismissConfirm() = _state.update { it.copy(confirming = false) }

    fun close() {
        val lines = parsedLines()?.takeIf { it.isNotEmpty() } ?: return
        if (_state.value.closing) return
        _state.update { it.copy(closing = true, confirming = false, closeFailure = null) }
        viewModelScope.launch {
            when (val result = repository.closeCount(_state.value.note, lines)) {
                is DeviceResult.Ok -> {
                    _state.update { ResaleCountState(result = result.value) }
                    onSaved()
                }
                is DeviceResult.Failed -> {
                    if (result.failure == AppFailure.Unauthorized) onUnauthorized()
                    _state.update { it.copy(closing = false, closeFailure = result.failure) }
                }
            }
        }
    }

    /** Pasangan id dan jumlah yang sah dari isian yang tidak kosong; null bila ada isian yang bukan jumlah. */
    private fun parsedLines(): List<Pair<String, String>>? {
        val lines = mutableListOf<Pair<String, String>>()
        for ((id, text) in _state.value.typed) {
            if (text.isBlank()) continue
            lines += id to (StockQuantity.parse(text) ?: return null)
        }
        return lines
    }
}
