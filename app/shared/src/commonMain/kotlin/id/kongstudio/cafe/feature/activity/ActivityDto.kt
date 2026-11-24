package id.kongstudio.cafe.feature.activity

import id.kongstudio.cafe.core.format.DateTimeFormat
import kotlinx.serialization.Serializable

@Serializable
internal class ActivityPageDto(val events: List<ActivityEventDto> = emptyList()) {
    /** Aktivitas dengan jenis atau waktu yang tidak dikenal dilewati, bukan menggagalkan seluruh daftar. */
    fun toModel(): List<ActivityEvent> = events.mapNotNull { it.toModel() }
}

@Serializable
internal class ActivityEventDto(
    val id: String,
    val action: String,
    val at: String,
    val subject: String? = null,
    val status: String? = null,
    val minutes: Int? = null,
) {
    fun toModel(): ActivityEvent? {
        val known = ActivityAction.entries.firstOrNull { it.key == action } ?: return null
        val stamp = DateTimeFormat.stamp(at) ?: return null
        return ActivityEvent(id = id, action = known, at = stamp, subject = subject, status = status, minutes = minutes)
    }
}
