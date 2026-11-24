package id.kongstudio.cafe.feature.dashboard

import id.kongstudio.cafe.core.format.WibStamp
import id.kongstudio.cafe.core.format.YearMonth

internal class ProfileInfo(
    val name: String,
    val roleName: String,
    val outletName: String?,
    val isActive: Boolean,
    val photoUrl: String?,
)

internal class ScheduleEntry(val roleName: String?)

/** Tugas pribadi diberikan ke satu orang, tugas rutin ke yang dijadwalkan di shiftnya, tugas outlet ke semua orang di outlet. */
internal enum class PendingKind { Personal, Routine, Outlet }

/** [caption] menggantikan batas waktu bila ada, misalnya rentang waktu tugas outlet. */
internal class PendingTask(val title: String, val due: WibStamp?, val kind: PendingKind, val caption: String? = null)

/** Ringkasan kehadiran bulan berjalan untuk kartu di dasbor. */
internal class AttendanceMonth(
    val month: YearMonth,
    val present: Int,
    val late: Int,
    val notPresent: Int,
    val workMinutes: Int,
    val overtimeMinutes: Int,
    val penalty: Long,
)
