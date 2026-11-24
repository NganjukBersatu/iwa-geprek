package id.kongstudio.cafe.feature.attendancelog

import id.kongstudio.cafe.core.format.YearMonth

internal enum class AttendanceStatus { Present, Late, Permit, Sick, Absent }

internal const val LOCATION_MODE_OUTSIDE = "outside"

internal class AttendanceDay(
    val date: String,
    val status: AttendanceStatus,
    val clockIn: String?,
    val clockOut: String?,
    val lateMinutes: Int,
    val shiftCode: String?,
    val roleName: String?,
    val workMinutes: Int?,
    val penalty: Long,
    val outsideScheduleReason: String?,
    val note: String?,
    val photoInUrl: String?,
    val photoOutUrl: String?,
    /** [LOCATION_MODE_OUTSIDE] berarti absen dilakukan di luar radius lokasi. */
    val modeIn: String?,
    val locationNoteIn: String?,
    val distanceIn: Double?,
    val modeOut: String?,
    val locationNoteOut: String?,
    val distanceOut: Double?,
    /** Akurasi GPS dan batas radius cabang (meter) saat absen. */
    val accuracyIn: Double?,
    val radiusIn: Int?,
    val accuracyOut: Double?,
    val radiusOut: Int?,
    val autoClosed: Boolean,
)

internal class AttendanceMonth(
    val month: YearMonth,
    val present: Int,
    val late: Int,
    val notPresent: Int,
    val penalty: Long,
    val days: List<AttendanceDay>,
)
