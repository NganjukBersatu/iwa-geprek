package id.kongstudio.cafe.feature.sessions

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.time.BusinessDay
import id.kongstudio.cafe.core.time.ShiftDay
import id.kongstudio.cafe.feature.devicesetup.DeviceResult
import id.kongstudio.cafe.offline.QueueCounts
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

internal enum class SessionSheet { None, Open, Close, SignOut }

internal data class SessionControlState(
    /** Status sesi sudah terbaca dari server; tanpa itu buka, tutup, dan keluar ditahan. */
    val known: Boolean = false,
    val active: ActiveSession? = null,
    val sheet: SessionSheet = SessionSheet.None,
    /** Rekap sebelum tutup; kosong sampai antrean bersih dan rekap terbaca dari server. */
    val recap: SessionRecap? = null,
    val submitting: Boolean = false,
    val failure: AppFailure? = null,
    /** Antrean pesanan milik karyawan ini saja; null sampai terbaca, supaya gerbang tidak lolos sebelum hitungan pertama. */
    val queue: QueueCounts? = null,
    /** Tutup sesi ini dimulai dari tombol keluar, jadi karyawan dilepas begitu sesi tertutup. */
    val signOutAfterClose: Boolean = false,
    /** Pesanan tertinggal dari sesi yang sudah ditutup; tidak kosong berarti modal pengingat tampil. */
    val leftBehind: List<LeftBehindOrder> = emptyList(),
)

/** Satu pintu sesi kas dan keluar dari tablet: keluar hanya setelah sesi tertutup, dan keduanya hanya setelah antrean pesanan karyawan ini bersih di server. */
internal class SessionControlViewModel(
    private val repository: SessionControlRepository,
    queue: Flow<QueueCounts>,
    /** Saluran /v2/live tersambung; status sesi dibaca ulang setiap kali server terjangkau lagi. */
    connected: Flow<Boolean>,
    private val onChanged: () -> Unit,
    private val onSignOut: () -> Unit,
    private val onUnauthorized: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(SessionControlState())
    val state: StateFlow<SessionControlState> = _state.asStateFlow()
    private var gate: Job? = null

    init {
        viewModelScope.launch {
            load()
            // Pengingat Tertinggal muncul setiap kali tablet dibuka dengan sesi yang berjalan.
            _state.value.active?.let { loadLeftBehind(it.id) }
        }
        viewModelScope.launch { queue.collect { counts -> _state.update { it.copy(queue = counts) } } }
        // Dibuka saat offline berarti status belum terbaca; tanpa membaca ulang, sesi yang berjalan tampak belum dibuka selamanya.
        viewModelScope.launch {
            connected.distinctUntilChanged().drop(1).filter { it }.collect {
                val before = _state.value.active?.id
                load()
                val after = _state.value.active?.id
                if (after != before) onChanged()
                if (after != null && after != before) loadLeftBehind(after)
            }
        }
    }

    /** Membaca ulang status sesi dari server, misalnya dari tombol coba lagi saat status belum terbaca. */
    fun reload() {
        viewModelScope.launch { load() }
    }

    fun showOpen() {
        _state.update { it.copy(sheet = SessionSheet.Open, failure = null) }
        viewModelScope.launch { load() }
    }

    fun showClose() = beginClose(signOutAfter = false)

    /** Tombol keluar: sesi terbuka ditutup dulu, tanpa sesi keluar setelah antrean bersih, dan [canHoldSession] false membuat status sesi yang belum terbaca tidak menahan. */
    fun signOut(canHoldSession: Boolean) {
        gate?.cancel()
        gate = viewModelScope.launch {
            load()
            val current = _state.value
            when {
                current.active != null -> beginClose(signOutAfter = true)
                !current.known && canHoldSession -> _state.update { it.copy(sheet = SessionSheet.SignOut, failure = null) }
                else -> {
                    if (_state.value.queue?.isEmpty != true) _state.update { it.copy(sheet = SessionSheet.SignOut, failure = null) }
                    awaitClearQueue()
                    _state.update { it.copy(sheet = SessionSheet.None) }
                    onSignOut()
                }
            }
        }
    }

    fun dismiss() {
        gate?.cancel()
        _state.update { it.copy(sheet = SessionSheet.None, failure = null, signOutAfterClose = false) }
    }

    fun submitOpen(openingCash: Long) {
        if (_state.value.submitting) return
        _state.update { it.copy(submitting = true, failure = null) }
        viewModelScope.launch {
            when (val result = repository.open(openingCash)) {
                is DeviceResult.Ok -> {
                    BusinessDay.follow(ShiftDay.Running(result.value.businessDay))
                    _state.update {
                        it.copy(submitting = false, known = true, active = result.value, sheet = SessionSheet.None)
                    }
                    onChanged()
                    loadLeftBehind(result.value.id)
                }
                is DeviceResult.Failed -> {
                    if (fail(result.failure)) return@launch
                    _state.update { it.copy(submitting = false, failure = result.failure) }
                }
            }
        }
    }

    fun submitClose(counted: CountedCash, note: String) {
        val current = _state.value
        val id = current.active?.id ?: return
        if (current.submitting || current.queue?.isEmpty != true || current.recap == null) return
        _state.update { it.copy(submitting = true, failure = null) }
        viewModelScope.launch {
            when (val result = repository.close(id, counted, note)) {
                is DeviceResult.Ok -> {
                    val signOut = _state.value.signOutAfterClose
                    BusinessDay.follow(ShiftDay.None)
                    _state.update {
                        it.copy(submitting = false, active = null, sheet = SessionSheet.None, signOutAfterClose = false)
                    }
                    onChanged()
                    if (signOut) onSignOut()
                }
                is DeviceResult.Failed -> {
                    if (fail(result.failure)) return@launch
                    _state.update { it.copy(submitting = false, failure = result.failure) }
                }
            }
        }
    }

    /** Nanti dan Tangani sekarang sama-sama menutup modal; pengingat muncul lagi di pembukaan berikutnya. */
    fun dismissLeftBehind() = _state.update { it.copy(leftBehind = emptyList()) }

    // Gagal dibaca tidak menahan apa pun; daftar pesanan Kasir tetap menampilkan pesanan tertinggal.
    private suspend fun loadLeftBehind(sessionId: String) {
        when (val result = repository.leftBehind(sessionId)) {
            is DeviceResult.Ok -> _state.update { it.copy(leftBehind = result.value) }
            is DeviceResult.Failed -> fail(result.failure)
        }
    }

    /** Rekap baru dibaca setelah antrean bersih, karena pesanan yang belum terkirim belum terhitung di sesi. */
    private fun beginClose(signOutAfter: Boolean) {
        gate?.cancel()
        _state.update {
            it.copy(sheet = SessionSheet.Close, failure = null, recap = null, signOutAfterClose = signOutAfter)
        }
        gate = viewModelScope.launch {
            load()
            awaitClearQueue()
            val id = _state.value.active?.id ?: return@launch
            when (val recap = repository.recap(id)) {
                is DeviceResult.Ok -> _state.update { it.copy(recap = recap.value) }
                is DeviceResult.Failed -> if (!fail(recap.failure)) _state.update { it.copy(failure = recap.failure) }
            }
        }
    }

    private suspend fun awaitClearQueue() {
        _state.first { it.queue?.isEmpty == true }
    }

    private suspend fun load() {
        when (val result = repository.active()) {
            is DeviceResult.Ok -> {
                BusinessDay.follow(result.value?.let { ShiftDay.Running(it.businessDay) } ?: ShiftDay.None)
                _state.update { it.copy(known = true, active = result.value) }
            }
            is DeviceResult.Failed -> {
                if (fail(result.failure)) return
                _state.update { it.copy(known = false) }
            }
        }
    }

    /** True bila token karyawan ditolak: perangkat meminta pindai ulang dan proses dihentikan. */
    private fun fail(failure: AppFailure): Boolean {
        if (failure != AppFailure.Unauthorized) return false
        onUnauthorized()
        return true
    }
}
