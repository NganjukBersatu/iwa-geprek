package id.kongstudio.cafe.feature.overtime

import id.kongstudio.cafe.core.format.DateTimeFormat
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal class OvertimeEntryDto(
    val id: String,
    @SerialName("started_at") val startedAt: String? = null,
    @SerialName("ended_at") val endedAt: String? = null,
    val minutes: Int = 0,
    val scheduled: Boolean = false,
    val note: String? = null,
) {
    fun toModel() = OvertimeEntry(
        id = id,
        start = DateTimeFormat.stamp(startedAt),
        end = DateTimeFormat.stamp(endedAt),
        minutes = minutes,
        scheduled = scheduled,
        note = note?.takeIf { it.isNotBlank() },
    )
}

@Serializable
internal class UnplannedOvertimeDto(
    @SerialName("started_at") val startedAt: String,
    @SerialName("ended_at") val endedAt: String,
    val note: String,
)
