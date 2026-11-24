package id.kongstudio.cafe.feature.notices

import id.kongstudio.cafe.core.format.DateTimeFormat
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

private const val KIND_TASK_OVERDUE = "task_overdue"
private const val KIND_DUE_CHANGED = "due_changed"

@Serializable
internal class NoticeDto(
    val id: String,
    val kind: String,
    val title: String,
    @SerialName("show_at") val showAt: String? = null,
) {
    fun toModel() = NoticeItem(
        id = id,
        kind = when (kind) {
            KIND_TASK_OVERDUE -> NoticeKind.TaskOverdue
            KIND_DUE_CHANGED -> NoticeKind.DueChanged
            else -> NoticeKind.TaskAssigned
        },
        title = title,
        showAt = DateTimeFormat.stamp(showAt),
    )
}

@Serializable
internal class ReadNoticesDto(val ids: List<String>)
