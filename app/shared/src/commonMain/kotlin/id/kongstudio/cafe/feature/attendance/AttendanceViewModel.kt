package id.kongstudio.cafe.feature.attendance

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.image.PhotoConverter
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.feature.location.DeviceLocation
import id.kongstudio.cafe.feature.location.LocationFix
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.attendance_key_reused
import id.kongstudio.cafe.resources.attendance_location_unavailable
import id.kongstudio.cafe.resources.attendance_no_active_schedule
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

internal data class AttendanceUiState(
    val state: AttendanceState? = null,
    val loading: Boolean = true,
    val failure: AppFailure? = null,
    /** Lembar absen yang sedang terbuka; null bila tertutup. */
    val sheet: ClockKind? = null,
    val submitting: Boolean = false,
    val submitError: UiText? = null,
    /** Absen yang baru berhasil dan sedang dirayakan; lembar absen tetap terbuka di bawahnya sampai selesai. */
    val celebration: ClockCelebration? = null,
    val acknowledging: Boolean = false,
    /** Jadwal yang baru dibuat lewat absen mandiri; absen datang memakainya. */
    val selfScheduledId: String? = null,
    /** Posisi yang dibaca saat lembar absen dibuka, untuk menampilkan jarak ke cabang sebelum memotret. */
    val preview: LocationFix? = null,
    val locating: Boolean = false,
) {
    /** Jarak posisi [preview] ke titik cabang; null bila salah satunya belum ada. */
    fun previewDistance(location: DeviceLocation): Double? {
        val fix = preview ?: return null
        val branch = state?.branch ?: return null
        val latitude = branch.latitude ?: return null
        val longitude = branch.longitude ?: return null
        return location.distanceMeters(fix, latitude, longitude)
    }
}

internal class AttendanceViewModel(
    private val repository: AttendanceRepository,
    val location: DeviceLocation,
    private val userName: String,
    private val onSessionExpired: () -> Unit,
) : ViewModel() {
    private val _state = MutableStateFlow(AttendanceUiState())
    val state: StateFlow<AttendanceUiState> = _state.asStateFlow()
    private var job: Job? = null
    /** Muatan percobaan absen terakhir, dipakai ulang apa adanya saat dicoba lagi karena server menolak kunci yang sama dengan isi berbeda. */
    private var attempt: ClockAttempt? = null

    /** Dipanggil tiap halaman dibuka agar status selalu terbaru. */
    fun load() {
        job?.cancel()
        _state.update { it.copy(loading = it.state == null, failure = null) }
        job = viewModelScope.launch {
            when (val result = repository.state()) {
                is ApiResult.Success -> _state.update { it.copy(state = result.value, loading = false) }
                ApiResult.Unauthorized -> onSessionExpired()
                is ApiResult.Failure -> _state.update { it.copy(loading = false, failure = result.failure) }
            }
        }
    }

    fun openSheet(kind: ClockKind) {
        attempt = null
        _state.update { it.copy(sheet = kind, submitError = null) }
        locate()
    }

    /** Membaca posisi untuk pratinjau jarak; dipanggil saat lembar dibuka dan saat karyawan meminta baca ulang. */
    fun locate() {
        if (_state.value.locating) return
        // Posisi dibaca ulang berarti isi absen berubah, jadi percobaan lama dan kuncinya dibuang.
        attempt = null
        _state.update { it.copy(locating = true) }
        viewModelScope.launch {
            val fix = location.current()
            _state.update { it.copy(preview = fix, locating = false) }
        }
    }

    fun closeSheet() {
        attempt = null
        _state.update { it.copy(sheet = null, submitError = null, selfScheduledId = null, preview = null) }
    }

    /** Setelah jadwal mandiri tersimpan, lembar absen datang langsung terbuka untuk jadwal itu. */
    fun startSelfScheduled(scheduleId: String) {
        _state.update { it.copy(sheet = ClockKind.In, submitError = null, selfScheduledId = scheduleId) }
        load()
        locate()
    }

    /** Membaca posisi lalu mengirim absen; foto dan keterangan datang dari lembar. */
    fun submit(photo: ByteArray, outside: Boolean, note: String) {
        val kind = _state.value.sheet ?: return
        if (_state.value.submitting) return
        // Absen datang selalu menyebut jadwal yang tampil di layar; backend hanya memeriksanya, tidak memilihkan.
        val scheduleId = if (kind == ClockKind.In) _state.value.selfScheduledId ?: _state.value.state?.schedule?.id else null
        if (kind == ClockKind.In && scheduleId == null) {
            failSubmit(UiText.Resource(Res.string.attendance_no_active_schedule))
            return
        }
        _state.update { it.copy(submitting = true, submitError = null) }
        viewModelScope.launch {
            val trimmedNote = note.trim().ifEmpty { null }
            // Coba ulang dengan foto, jadwal, dan catatan yang sama memakai muatan dan kunci yang sama persis, tanpa membaca posisi atau memotret lagi.
            val reusable = attempt?.takeIf { it.matches(kind, scheduleId, photo, outside, trimmedNote) }
            val current = reusable ?: run {
                val fix = location.current()
                if (fix == null) {
                    failSubmit(UiText.Resource(Res.string.attendance_location_unavailable))
                    return@launch
                }
                val stamp = PhotoStamps.build(userName, _state.value.state?.branch, fix, location, outside, trimmedNote)
                ClockAttempt(
                    kind = kind,
                    scheduleId = scheduleId,
                    rawPhoto = photo,
                    outside = outside,
                    note = trimmedNote,
                    request = ClockRequest(
                        scheduleId = scheduleId,
                        // Cap gagal dibuat tidak menghalangi absen; foto dikirim apa adanya.
                        photo = PhotoConverter.stamp(photo, stamp) ?: photo,
                        fix = fix,
                        outside = outside,
                        note = trimmedNote,
                        idempotencyKey = newAttemptKey(),
                    ),
                ).also { attempt = it }
            }
            when (val result = repository.clock(kind, current.request)) {
                is WriteResult.Success -> {
                    attempt = null
                    celebrate(kind)
                }
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Failure -> {
                    val failure = result.failure
                    // Kunci yang sama dengan isi berbeda: percobaan dibuang, pesan tampil, dan status dimuat ulang dari server.
                    val reused = failure is AppFailure.Rejected && failure.serverCode == KEY_REUSED_CODE
                    if (reused) attempt = null
                    failSubmit(if (reused) UiText.Resource(Res.string.attendance_key_reused) else UiText.Failed(failure))
                    load()
                }
            }
        }
    }

    /** Menutup perayaan beserta lembar absen di bawahnya, lalu memuat ulang status. */
    fun finishCelebration() {
        attempt = null
        _state.update { it.copy(celebration = null, sheet = null, submitting = false, selfScheduledId = null, preview = null) }
        load()
    }

    /** Memuat status terbaru agar jam yang dirayakan sama dengan yang tercatat di server. */
    private suspend fun celebrate(kind: ClockKind) {
        val fresh = (repository.state() as? ApiResult.Success)?.value
        val record = fresh?.record
        val minutes = when (kind) {
            ClockKind.In -> record?.clockIn?.let { minutesOfDay(it.time) }
            ClockKind.Out -> record?.workMinutes
        }
        _state.update { it.copy(state = fresh ?: it.state, celebration = ClockCelebration(kind, minutes)) }
    }

    private fun minutesOfDay(time: String) = time.substring(0, 2).toInt() * 60 + time.substring(3, 5).toInt()

    /** Menandai semua pemberitahuan yang tampil sudah dilihat, lalu memuat ulang. */
    fun acknowledgeNotices() {
        val ids = _state.value.state?.notices.orEmpty().map { it.id }
        if (ids.isEmpty() || _state.value.acknowledging) return
        _state.update { it.copy(acknowledging = true) }
        viewModelScope.launch {
            when (repository.acknowledge(ids)) {
                WriteResult.Unauthorized -> onSessionExpired()
                is WriteResult.Success -> {
                    // Pemberitahuan langsung disembunyikan agar tombolnya tidak bisa diketuk lagi selama memuat ulang.
                    _state.update { it.copy(acknowledging = false, state = it.state?.withoutNotices()) }
                    load()
                }
                is WriteResult.Failure -> _state.update { it.copy(acknowledging = false) }
            }
        }
    }

    private fun failSubmit(text: UiText) = _state.update { it.copy(submitting = false, submitError = text) }
}

@OptIn(ExperimentalUuidApi::class)
private fun newAttemptKey(): String = Uuid.random().toString()

private const val KEY_REUSED_CODE = "IDEMPOTENCY_KEY_REUSED"

/** Satu percobaan absen: isi mentah yang dipilih karyawan dan muatan yang sudah dibangun darinya, termasuk kuncinya. */
private class ClockAttempt(
    val kind: ClockKind,
    val scheduleId: String?,
    val rawPhoto: ByteArray,
    val outside: Boolean,
    val note: String?,
    val request: ClockRequest,
) {
    fun matches(kind: ClockKind, scheduleId: String?, photo: ByteArray, outside: Boolean, note: String?): Boolean =
        this.kind == kind && this.scheduleId == scheduleId && this.outside == outside && this.note == note && rawPhoto.contentEquals(photo)
}
