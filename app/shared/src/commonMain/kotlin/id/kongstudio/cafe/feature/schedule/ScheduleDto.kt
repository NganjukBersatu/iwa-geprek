package id.kongstudio.cafe.feature.schedule

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal class MonthBoardDto(
    @SerialName("outlet_name") val outletName: String? = null,
    val assignments: List<AssignmentDto> = emptyList(),
    @SerialName("days_off") val daysOff: List<DayOffDto> = emptyList(),
    @SerialName("shift_codes") val shiftCodes: List<ShiftCodeDto> = emptyList(),
)

@Serializable
internal class AssignmentDto(
    val date: String,
    @SerialName("user_id") val userId: String,
    @SerialName("user_username") val userName: String = "",
    @SerialName("shift_code_id") val codeId: String? = null,
    @SerialName("role_name") val roleName: String? = null,
    val note: String? = null,
)

@Serializable
internal class DayOffDto(
    val date: String,
    @SerialName("user_id") val userId: String,
    @SerialName("user_username") val userName: String = "",
    @SerialName("shift_code_id") val codeId: String? = null,
    val note: String? = null,
)

@Serializable
internal class ShiftCodeDto(
    val id: String,
    val code: String,
    val category: String? = null,
    @SerialName("start_clock") val start: String? = null,
    @SerialName("end_clock") val end: String? = null,
    @SerialName("overtime_start_clock") val overtimeStart: String? = null,
    @SerialName("overtime_end_clock") val overtimeEnd: String? = null,
    val color: String? = null,
    @SerialName("is_day_off") val off: Boolean = false,
) {
    fun toModel() = ShiftCode(
        id = id,
        code = code,
        category = category?.takeIf { it.isNotBlank() },
        start = start,
        end = end,
        overtimeStart = overtimeStart,
        overtimeEnd = overtimeEnd,
        color = color,
        off = off,
    )
}
