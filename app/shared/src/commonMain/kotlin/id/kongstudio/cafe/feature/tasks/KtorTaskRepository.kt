package id.kongstudio.cafe.feature.tasks

import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import id.kongstudio.cafe.core.network.appendFile
import id.kongstudio.cafe.core.network.multipart
import id.kongstudio.cafe.ui.component.mediafield.PickedMedia
import io.ktor.client.call.body
import io.ktor.client.request.parameter
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.HttpMethod
import io.ktor.http.contentType
import io.ktor.client.request.forms.FormBuilder

private const val TASKS = "/v2/tasks"
private const val FILES_FIELD = "files"

internal class KtorTaskRepository(private val api: ApiCaller) : TaskRepository {

    override suspend fun load(query: TaskQuery): ApiResult<TaskPage> =
        api.read(
            path = TASKS,
            configure = {
                parameter("status", query.filter.apiValue)
                query.dateFrom?.let { parameter("date_from", it) }
                query.dateTo?.let { parameter("date_to", it) }
                query.outletId?.let { parameter("outlet_id", it) }
                query.assigneeId?.let { parameter("assignee_id", it) }
                if (query.search.isNotBlank()) parameter("q", query.search.trim())
                parameter("page", query.page + 1)
                parameter("size", TaskPageSize)
            },
        ) { it.body<TaskPageDto>().toModel() }

    override suspend fun options(outletId: String?): ApiResult<TaskOptions> =
        api.read(
            path = "$TASKS/options",
            configure = { outletId?.let { parameter("outlet_id", it) } },
        ) { it.body<TaskOptionsDto>().toModel() }

    override suspend fun sourceRun(taskId: String): ApiResult<SourceRun> =
        api.read(path = "$TASKS/$taskId/source-run") { it.body<SourceRunDetailDto>().toModel() }

    override suspend fun create(task: NewTask): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Post,
            path = TASKS,
            configure = {
                multipart {
                    append("title", task.title.trim())
                    if (task.description.isNotBlank()) append("description", task.description.trim())
                    task.assigneeId?.let { append("assignee_id", it) }
                    task.due?.let { append("due_at", it) }
                    append("complete", task.complete.toString())
                    appendMedia(task.media)
                }
            },
            parse = { },
        )

    override suspend fun update(
        taskId: String,
        title: String,
        description: String,
        due: String?,
    ): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Patch,
            path = "$TASKS/$taskId",
            configure = {
                contentType(ContentType.Application.Json)
                setBody(TaskUpdateDto(title = title.trim(), description = description.trim(), dueAt = due))
            },
            parse = { },
        )

    override suspend fun complete(taskId: String, note: String, media: List<PickedMedia>): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Post,
            path = "$TASKS/$taskId/complete",
            configure = {
                multipart {
                    if (note.isNotBlank()) append("note", note.trim())
                    appendMedia(media)
                }
            },
            parse = { },
        )

    override suspend fun fixCompletion(taskId: String, note: String): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Patch,
            path = "$TASKS/$taskId/completion",
            configure = {
                contentType(ContentType.Application.Json)
                setBody(CompletionDto(note = note.trim()))
            },
            parse = { },
        )

    override suspend fun addAttachments(taskId: String, media: List<PickedMedia>): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Post,
            path = "$TASKS/$taskId/attachments",
            configure = { multipart { appendMedia(media) } },
            parse = { },
        )

    override suspend fun removeAttachment(taskId: String, attachmentId: String): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Delete,
            path = "$TASKS/$taskId/attachments/$attachmentId",
            configure = {},
            parse = { },
        )

    override suspend fun delete(taskId: String): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Delete,
            path = "$TASKS/$taskId",
            configure = {},
            parse = { },
        )
}

private fun FormBuilder.appendMedia(media: List<PickedMedia>) {
    media.forEach { appendFile(FILES_FIELD, it.bytes, it.mimeType, it.fileName) }
}
