package id.kongstudio.cafe.feature.attendance

import id.kongstudio.cafe.core.format.WibStamp
import id.kongstudio.cafe.feature.location.LocationFix

internal enum class ClockKind { In, Out }

/** Penugasan yang berlaku untuk karyawan, dengan jam mulai dan selesai nyata; [id] dikirim saat absen datang. */
internal class ScheduleSummary(
    val id: String?,
    val code: String?,
    val colorHex: String?,
    val startsAt: WibStamp?,
    val endsAt: WibStamp?,
)

internal class AttendanceRecord(
    val late: Boolean,
    val clockIn: WibStamp?,
    val clockOut: WibStamp?,
    val autoClosed: Boolean,
    val photoInUrl: String?,
    val photoOutUrl: String?,
    /** Jam kerja di dalam jam shift, dihitung backend. */
    val workMinutes: Int?,
)

/** Absen yang ditutup sistem dan belum diberitahukan ke karyawan. */
internal class AutoCloseNotice(
    val id: String,
    val clockIn: WibStamp?,
    val clockOut: WibStamp?,
)

internal enum class ClockInBlockReason { NotOpenYet, AlreadyUsed, Ended, NoPermission, NoSchedule }

/** Alasan absen datang belum bisa dilakukan; [at] jam dibukanya absen atau jam jadwal berakhir. */
internal class ClockInBlock(
    val reason: ClockInBlockReason,
    val schedule: ScheduleSummary?,
    val at: WibStamp?,
)

/** Cabang patokan absen berikutnya; titik atau radius yang kosong berarti jarak tidak dinilai. */
internal class AttendanceBranch(
    val name: String,
    val latitude: Double?,
    val longitude: Double?,
    val radiusMeters: Int?,
)

internal class AttendanceState(
    val canClockIn: Boolean,
    val canClockOut: Boolean,
    val record: AttendanceRecord?,
    val schedule: ScheduleSummary?,
    val notices: List<AutoCloseNotice>,
    val clockInBlock: ClockInBlock?,
    /** Tidak punya jadwal hari ini, jadi absen datang dimulai dengan absen mandiri. */
    val canSelfSchedule: Boolean,
    val branch: AttendanceBranch?,
) {
    fun withoutNotices() =
        AttendanceState(canClockIn, canClockOut, record, schedule, emptyList(), clockInBlock, canSelfSchedule, branch)
}

/** Absen yang baru berhasil; [minutes] adalah jam datang (menit sejak 00.00) atau durasi kerja, null bila belum terbaca. */
internal class ClockCelebration(val kind: ClockKind, val minutes: Int?)

/** Isi satu absen: foto, posisi, keterangan bila di luar lokasi, dan [scheduleId] jadwal yang diabsen (hanya absen datang). */
internal class ClockRequest(
    val scheduleId: String?,
    val photo: ByteArray,
    val fix: LocationFix,
    val outside: Boolean,
    val note: String?,
    /** Kunci acak satu percobaan absen; dikirim ulang saat dicoba lagi supaya server tidak mencatat absen ganda. */
    val idempotencyKey: String,
)
