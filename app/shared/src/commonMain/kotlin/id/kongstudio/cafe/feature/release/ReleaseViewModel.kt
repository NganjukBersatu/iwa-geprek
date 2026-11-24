package id.kongstudio.cafe.feature.release

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

// Ringkasan pembaruan diminta sekali setiap karyawan memegang tablet; gagal membaca berarti tidak ditampilkan sampai dibuka lagi.
internal class ReleaseViewModel(
    private val repository: ReleaseRepository,
    private val version: String,
    private val onUnauthorized: () -> Unit,
) : ViewModel() {
    private val _open = MutableStateFlow(false)
    val open: StateFlow<Boolean> = _open.asStateFlow()

    init {
        viewModelScope.launch {
            when (val result = repository.read(version)) {
                is DeviceResult.Ok -> _open.value = !result.value
                is DeviceResult.Failed -> if (result.failure is AppFailure.Unauthorized) onUnauthorized()
            }
        }
    }

    // Lembar langsung tertutup; gagal menandai hanya membuat ringkasan muncul lagi nanti.
    fun close() {
        _open.value = false
        viewModelScope.launch { repository.markRead(version) }
    }
}
