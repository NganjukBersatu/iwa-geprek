package id.kongstudio.cafe.feature.devicesetup

import id.kongstudio.cafe.ui.theme.window.FormFactor
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

private const val PhoneCode = "phone"
private const val TabletCode = "tablet"

/** Pilihan tampilan perangkat dari web admin; null berarti app menebak sendiri dari ukuran layar. */
internal class DeviceLayout {
    private val _formFactor = MutableStateFlow<FormFactor?>(null)
    val formFactor: StateFlow<FormFactor?> = _formFactor.asStateFlow()

    /** [code] dari header jawaban server atau dari simpanan perangkat; nilai yang tidak dikenal dianggap otomatis. */
    fun observe(code: String) {
        _formFactor.value = when (code) {
            PhoneCode -> FormFactor.Phone
            TabletCode -> FormFactor.Tablet
            else -> null
        }
    }
}
