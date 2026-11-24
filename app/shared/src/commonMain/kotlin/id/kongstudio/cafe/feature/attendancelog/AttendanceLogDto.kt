package id.kongstudio.cafe.feature.attendancelog

import id.kongstudio.cafe.core.format.YearMonth
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal class AttendanceSummaryDto(
    val month: String,
    val totals: AttendanceTotalsDto = AttendanceTotalsDto(),
    val days: List<AttendanceDayDto> = emptyList(),
) {
    fun toModel(): AttendanceMonth {
        val parts = month.split('-')
        return AttendanceMonth(
            month = YearMonth(parts[0].toInt(), parts[1].toInt()),
            present = totals.present + totals.late,
            late = totals.late,
            notPresent = totals.leave + totals.sick + totals.absent,
            penalty = totals.penalty,
            days = days.map { it.toModel() }.sortedByDescending { it.date },
        )
    }
}

@Serializable
internal class AttendanceTotalsDto(
    val present: Int = 0,
    val late: Int = 0,
    val leave: Int = 0,
    val sick: Int = 0,
    val absent: Int = 0,
    val penalty: Long = 0,
)

@Serializable
internal class AttendanceLocationDto(
    val mode: String? = null,
    val note: String? = null,
    @SerialName("distance_meters") val distanceMeters: Double? = null,
    @SerialName("accuracy_meters") val accuracyMeters: Double? = null,
    @SerialName("radius_meters") val radiusMeters: Int? = null,
)

@Serializable
internal class AttendanceDayDto(
    val date: String,
    val status: String,
    @SerialName("shift_code") val shiftCode: String? = null,
    @SerialName("role_name") val roleName: String? = null,
    @SerialName("clock_in_at") val clockIn: String? = null,
    @SerialName("clock_out_at") val clockOut: String? = null,
    @SerialName("late_minutes") val lateMinutes: Int = 0,
    @SerialName("work_minutes") val workMinutes: Int? = null,
    val penalty: Long = 0,
    val note: String? = null,
    @SerialName("outside_schedule_reason") val outsideScheduleReason: String? = null,
    @SerialName("auto_closed") val autoClosed: Boolean = false,
    @SerialName("clock_in_photo_url") val photoInUrl: String? = null,
    @SerialName("clock_out_photo_url") val photoOutUrl: String? = null,
    @SerialName("clock_in_location") val locationIn: AttendanceLocationDto? = null,
    @SerialName("clock_out_location") val locationOut: AttendanceLocationDto? = null,
) {
    fun toModel() = AttendanceDay(
        date = date,
        status = when (status) {
            "hadir" -> AttendanceStatus.Present
            "telat" -> AttendanceStatus.Late
            "izin" -> AttendanceStatus.Permit
            "sakit" -> AttendanceStatus.Sick
            else -> AttendanceStatus.Absent
        },
        clockIn = clockIn,
        clockOut = clockOut,
        lateMinutes = lateMinutes,
        shiftCode = shiftCode,
        roleName = roleName,
        workMinutes = workMinutes,
        penalty = penalty,
        outsideScheduleReason = outsideScheduleReason,
        note = note,
        photoInUrl = photoInUrl,
        photoOutUrl = photoOutUrl,
        modeIn = locationIn?.mode,
        locationNoteIn = locationIn?.note,
        distanceIn = locationIn?.distanceMeters,
        modeOut = locationOut?.mode,
        locationNoteOut = locationOut?.note,
        distanceOut = locationOut?.distanceMeters,
        accuracyIn = locationIn?.accuracyMeters,
        radiusIn = locationIn?.radiusMeters,
        accuracyOut = locationOut?.accuracyMeters,
        radiusOut = locationOut?.radiusMeters,
        autoClosed = autoClosed,
    )
}
