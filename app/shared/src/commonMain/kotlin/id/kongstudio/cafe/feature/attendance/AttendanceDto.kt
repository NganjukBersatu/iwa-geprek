package id.kongstudio.cafe.feature.attendance

import id.kongstudio.cafe.core.format.DateTimeFormat
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

private const val STATUS_LATE = "telat"
private const val BLOCK_NOT_OPEN_YET = "not_open_yet"
private const val BLOCK_ALREADY_USED = "already_used"
private const val BLOCK_ENDED = "ended"
private const val BLOCK_NO_PERMISSION = "no_permission"

@Serializable
internal class ScheduleSummaryDto(
    val id: String? = null,
    val code: String? = null,
    val color: String? = null,
    @SerialName("starts_at") val startsAt: String? = null,
    @SerialName("ends_at") val endsAt: String? = null,
) {
    fun toModel() = ScheduleSummary(
        id = id,
        code = code,
        colorHex = color,
        startsAt = DateTimeFormat.stamp(startsAt),
        endsAt = DateTimeFormat.stamp(endsAt),
    )
}

@Serializable
internal class AttendanceDto(
    val status: String = "",
    @SerialName("clock_in_at") val clockInAt: String? = null,
    @SerialName("clock_out_at") val clockOutAt: String? = null,
    @SerialName("auto_closed") val autoClosed: Boolean = false,
    @SerialName("clock_in_photo_url") val clockInPhotoUrl: String? = null,
    @SerialName("clock_out_photo_url") val clockOutPhotoUrl: String? = null,
    @SerialName("work_minutes") val workMinutes: Int? = null,
) {
    fun toModel() = AttendanceRecord(
        late = status == STATUS_LATE,
        clockIn = DateTimeFormat.stamp(clockInAt),
        clockOut = DateTimeFormat.stamp(clockOutAt),
        autoClosed = autoClosed,
        photoInUrl = clockInPhotoUrl,
        photoOutUrl = clockOutPhotoUrl,
        workMinutes = workMinutes,
    )
}

@Serializable
internal class AutoCloseNoticeDto(
    val id: String,
    @SerialName("clock_in_at") val clockInAt: String? = null,
    @SerialName("clock_out_at") val clockOutAt: String? = null,
) {
    fun toModel() = AutoCloseNotice(
        id = id,
        clockIn = DateTimeFormat.stamp(clockInAt),
        clockOut = DateTimeFormat.stamp(clockOutAt),
    )
}

@Serializable
internal class ClockInBlockDto(
    val reason: String,
    val schedule: ScheduleSummaryDto? = null,
    val at: String? = null,
) {
    fun toModel() = ClockInBlock(
        reason = when (reason) {
            BLOCK_NOT_OPEN_YET -> ClockInBlockReason.NotOpenYet
            BLOCK_ALREADY_USED -> ClockInBlockReason.AlreadyUsed
            BLOCK_ENDED -> ClockInBlockReason.Ended
            BLOCK_NO_PERMISSION -> ClockInBlockReason.NoPermission
            else -> ClockInBlockReason.NoSchedule
        },
        schedule = schedule?.toModel(),
        at = DateTimeFormat.stamp(at),
    )
}

@Serializable
internal class BranchDto(
    val name: String = "",
    val latitude: Double? = null,
    val longitude: Double? = null,
    @SerialName("radius_meters") val radiusMeters: Int? = null,
) {
    fun toModel() = AttendanceBranch(name = name, latitude = latitude, longitude = longitude, radiusMeters = radiusMeters)
}

@Serializable
internal class AttendanceStateDto(
    @SerialName("can_clock_in") val canClockIn: Boolean = false,
    @SerialName("can_clock_out") val canClockOut: Boolean = false,
    val attendance: AttendanceDto? = null,
    val schedule: ScheduleSummaryDto? = null,
    @SerialName("auto_close_notices") val notices: List<AutoCloseNoticeDto> = emptyList(),
    @SerialName("clock_in_block") val clockInBlock: ClockInBlockDto? = null,
    @SerialName("can_self_schedule") val canSelfSchedule: Boolean = false,
    val branch: BranchDto? = null,
) {
    fun toModel() = AttendanceState(
        canClockIn = canClockIn,
        canClockOut = canClockOut,
        record = attendance?.toModel(),
        schedule = schedule?.toModel(),
        notices = notices.map { it.toModel() },
        clockInBlock = clockInBlock?.toModel(),
        canSelfSchedule = canSelfSchedule,
        branch = branch?.toModel(),
    )
}

@Serializable
internal class AcknowledgeDto(val ids: List<String>)
