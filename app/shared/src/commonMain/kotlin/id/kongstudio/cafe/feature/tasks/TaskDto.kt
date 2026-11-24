package id.kongstudio.cafe.feature.tasks

import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.ui.component.attachmentgallery.RemoteAttachment
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

private const val VideoKind = "video"

@Serializable
internal class TaskPageDto(
    val items: List<TaskItemDto> = emptyList(),
    val total: Int = 0,
) {
    fun toModel() = TaskPage(items = items.map { it.toModel() }, total = total)
}

@Serializable
internal class TaskItemDto(
    val id: String,
    val status: String,
    val title: String,
    val description: String? = null,
    val outlet: OutletDto? = null,
    val assignee: PersonDto? = null,
    val creator: PersonDto? = null,
    @SerialName("due_at") val dueAt: String? = null,
    @SerialName("completion_note") val doneNote: String? = null,
    @SerialName("completed_at") val doneAt: String? = null,
    val attachments: List<AttachmentDto> = emptyList(),
    @SerialName("source_run") val sourceRun: SourceRunDto? = null,
    @SerialName("follow_up_number") val followUpNumber: Int? = null,
    @SerialName("follow_up_total") val followUpTotal: Int? = null,
    val mine: Boolean = false,
    @SerialName("can_edit") val canEdit: Boolean = false,
    @SerialName("can_complete") val canComplete: Boolean = false,
    @SerialName("can_fix") val canFix: Boolean = false,
    @SerialName("can_delete") val canDelete: Boolean? = null,
) {
    fun toModel() = TaskItem(
        id = id,
        title = title,
        description = description?.takeIf { it.isNotBlank() },
        outletName = outlet?.name,
        creatorName = creator?.label,
        assigneeName = assignee?.label,
        due = DateTimeFormat.stamp(dueAt),
        done = status == TaskFilter.Done.apiValue,
        doneNote = doneNote?.takeIf { it.isNotBlank() },
        doneAt = DateTimeFormat.stamp(doneAt),
        attachments = attachments.map { it.toModel() },
        followUp = sourceRun?.let { run ->
            TaskFollowUp(batchName = run.batchName, day = run.day, number = followUpNumber ?: 1, total = followUpTotal ?: 1)
        },
        mine = mine,
        canEdit = canEdit,
        canComplete = canComplete,
        canFix = canFix,
        // Server lama belum mengirim hak hapus; di sana hanya yang boleh mengubah yang boleh menghapus.
        canDelete = canDelete ?: canEdit,
    )
}

@Serializable
internal class SourceRunDto(
    @SerialName("batch_name") val batchName: String,
    val day: String,
)

@Serializable
internal class CompletionDto(val note: String)

@Serializable
internal class SourceRunDetailDto(
    @SerialName("batch_name") val batchName: String,
    val day: String,
    @SerialName("outlet_name") val outletName: String,
    @SerialName("completed_by") val completedBy: String? = null,
    @SerialName("completed_at") val completedAt: String? = null,
    val problems: Int = 0,
    val answers: List<SourceAnswerDto> = emptyList(),
) {
    fun toModel() = SourceRun(
        batchName = batchName,
        day = day,
        outletName = outletName,
        completedBy = completedBy,
        completedAt = DateTimeFormat.stamp(completedAt),
        problems = problems,
        answers = answers.map { SourceAnswer(label = it.label, kind = it.kind, value = it.value, photoUrl = it.photoUrl) },
    )
}

@Serializable
internal class SourceAnswerDto(
    val label: String,
    val kind: String,
    val value: String? = null,
    @SerialName("photo_url") val photoUrl: String? = null,
)

@Serializable
internal class AttachmentDto(
    val id: String,
    val kind: String,
    val url: String,
    val removable: Boolean = false,
) {
    fun toModel() = RemoteAttachment(id = id, isVideo = kind == VideoKind, url = url, removable = removable)
}

@Serializable
internal class PersonDto(
    val id: String,
    val name: String? = null,
    val username: String = "",
) {
    val label: String get() = name?.takeIf(String::isNotBlank) ?: username

    fun toModel() = TaskPerson(id = id, name = label)
}

@Serializable
internal class OutletDto(
    val id: String,
    val name: String,
) {
    fun toModel() = TaskOutlet(id = id, name = name)
}

@Serializable
internal class TaskOptionsDto(
    val outlets: List<OutletDto> = emptyList(),
    val assignees: List<PersonDto> = emptyList(),
    @SerialName("can_manage") val canManage: Boolean = false,
) {
    fun toModel() = TaskOptions(
        outlets = outlets.map { it.toModel() },
        assignees = assignees.map { it.toModel() },
        canManage = canManage,
    )
}

@Serializable
internal class TaskUpdateDto(
    val title: String,
    val description: String,
    @SerialName("due_at") val dueAt: String? = null,
)
