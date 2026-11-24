package id.kongstudio.cafe.feature.dashboard

import id.kongstudio.cafe.core.format.YearMonth
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal class ProfileDto(
    val name: String? = null,
    val username: String,
    @SerialName("role_name") val roleName: String,
    @SerialName("outlet_name") val outletName: String? = null,
    @SerialName("is_active") val isActive: Boolean = true,
    @SerialName("photo_url") val photoUrl: String? = null,
) {
    fun toModel() = ProfileInfo(
        name = name?.takeIf { it.isNotBlank() } ?: username,
        roleName = roleName,
        outletName = outletName,
        isActive = isActive,
        photoUrl = photoUrl,
    )
}

@Serializable
internal class ScheduleDto(
    @SerialName("role_name") val roleName: String? = null,
) {
    fun toModel() = ScheduleEntry(roleName)
}

@Serializable
internal class TaskPageDto(val items: List<TaskDto> = emptyList())

@Serializable
internal class TaskDto(
    val status: String,
    val title: String,
    @SerialName("due_at") val dueAt: String? = null,
)

@Serializable
internal class AttendanceSummaryDto(
    val month: String,
    val totals: AttendanceTotalsDto = AttendanceTotalsDto(),
) {
    fun toModel(): AttendanceMonth {
        val parts = month.split('-')
        return AttendanceMonth(
            month = YearMonth(parts[0].toInt(), parts[1].toInt()),
            present = totals.present + totals.late,
            late = totals.late,
            notPresent = totals.leave + totals.sick + totals.absent,
            workMinutes = totals.workMinutes,
            overtimeMinutes = totals.overtimeMinutes,
            penalty = totals.penalty,
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
    @SerialName("work_minutes") val workMinutes: Int = 0,
    @SerialName("overtime_minutes") val overtimeMinutes: Int = 0,
    val penalty: Long = 0,
)
