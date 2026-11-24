package id.kongstudio.cafe.feature.attendance.selfschedule

import id.kongstudio.cafe.core.format.DateTimeFormat
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal class SelfScheduleChoiceDto(val id: String, val name: String) {
    fun toModel() = SelfScheduleChoice(id, name)
}

@Serializable
internal class ShiftSuggestionDto(
    @SerialName("shift_code_id") val shiftCodeId: String,
    val code: String,
    @SerialName("starts_at") val startsAt: String? = null,
    @SerialName("ends_at") val endsAt: String? = null,
) {
    fun toModel() = ShiftSuggestion(
        shiftCodeId = shiftCodeId,
        code = code,
        startsAt = DateTimeFormat.stamp(startsAt),
        endsAt = DateTimeFormat.stamp(endsAt),
    )
}

@Serializable
internal class SelfScheduleOptionsDto(
    val outlets: List<SelfScheduleChoiceDto> = emptyList(),
    val roles: List<SelfScheduleChoiceDto> = emptyList(),
    val suggestions: List<ShiftSuggestionDto> = emptyList(),
) {
    fun toModel() = SelfScheduleOptions(
        outlets = outlets.map { it.toModel() },
        roles = roles.map { it.toModel() },
        suggestions = suggestions.map { it.toModel() },
    )
}

@Serializable
internal class SelfScheduleRequestDto(
    @SerialName("outlet_id") val outletId: String,
    @SerialName("role_id") val roleId: String,
    @SerialName("shift_code_id") val shiftCodeId: String,
    val reason: String? = null,
)

@Serializable
internal class CreatedScheduleDto(val id: String)
