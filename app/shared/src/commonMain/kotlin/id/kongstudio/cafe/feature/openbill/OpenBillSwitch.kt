package id.kongstudio.cafe.feature.openbill

import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.offline.OfflineStore
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

private const val EnabledKey = "openbill.enabled"
private const val On = "on"
private const val Off = "off"

/** Saklar Open Bill milik tablet ini: disimpan di tablet, tidak lewat server, dan mati sampai dinyalakan dari menu Perangkat. */
internal class OpenBillSwitch(private val store: OfflineStore) {
    private val state = MutableStateFlow(false)
    val enabled: StateFlow<Boolean> = state

    /** Membaca pilihan tersimpan; tanpa pilihan tersimpan saklar mati. */
    suspend fun load() {
        val saved = runCatching { store.getCache(EnabledKey)?.body }.getOrNull()
        state.value = saved == On
    }

    suspend fun set(enabled: Boolean) {
        state.value = enabled
        // Gagal menyimpan berarti pilihan hilang saat aplikasi dibuka ulang; selama terbuka tetap mengikuti pilihan.
        runCatching { store.putCache(EnabledKey, if (enabled) On else Off, ServerClock.nowEpochSeconds()) }
    }
}
