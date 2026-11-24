package id.kongstudio.cafe.feature.dayplan

import id.kongstudio.cafe.core.format.DateTimeFormat
import kotlin.time.ExperimentalTime
import kotlin.time.Instant
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

private const val KIND_WORK = "work"
private const val KIND_SCHEDULED_OVERTIME = "scheduled_overtime"
private const val KIND_UNPLANNED_OVERTIME = "unplanned_overtime"
private const val UTC_SUFFIX = "Z"

@Serializable
internal class SegmentDto(
    val kind: String,
    @SerialName("starts_at") val startsAt: String,
    @SerialName("ends_at") val endsAt: String,
    val minutes: Int,
    val code: String? = null,
    val color: String? = null,
) {
    fun toModel(): DaySegment? {
        val kind = when (kind) {
            KIND_WORK -> SegmentKind.Work
            KIND_SCHEDULED_OVERTIME -> SegmentKind.ScheduledOvertime
            KIND_UNPLANNED_OVERTIME -> SegmentKind.UnplannedOvertime
            else -> return null
        }
        val startEpoch = epochOf(startsAt) ?: return null
        val endEpoch = epochOf(endsAt) ?: return null
        return DaySegment(
            kind = kind,
            startEpoch = startEpoch,
            endEpoch = endEpoch,
            start = DateTimeFormat.stampAt(startEpoch),
            end = DateTimeFormat.stampAt(endEpoch),
            minutes = minutes,
            code = code,
            colorHex = color,
        )
    }
}

@Serializable
internal class DayPlanDto(
    val segments: List<SegmentDto> = emptyList(),
    @SerialName("scheduled_overtime") val scheduledOvertime: SegmentDto? = null,
) {
    fun toModel() = DayPlan(
        segments = segments.mapNotNull { it.toModel() }.sortedBy { it.startEpoch },
        scheduledOvertime = scheduledOvertime?.toModel(),
    )
}

/** Stempel tanpa zona dibaca sebagai UTC seperti yang disimpan server. */
@OptIn(ExperimentalTime::class)
private fun epochOf(iso: String): Long? {
    val zoned = if (iso.endsWith(UTC_SUFFIX) || iso.substringAfter('T').any { it == '+' || it == '-' }) iso else iso + UTC_SUFFIX
    return runCatching { Instant.parse(zoned).epochSeconds }.getOrNull()
}
