package id.kongstudio.cafe.feature.leave

import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import id.kongstudio.cafe.core.network.appendFile
import id.kongstudio.cafe.core.network.multipart
import io.ktor.client.call.body
import io.ktor.http.HttpMethod

private const val REQUESTS = "/v2/leave/requests"

internal class KtorLeaveRepository(private val api: ApiCaller) : LeaveRepository {

    override suspend fun load(): ApiResult<List<LeaveRequest>> =
        api.read("$REQUESTS/mine") { response ->
            response.body<List<LeaveResponseDto>>().map { it.toModel() }
        }

    override suspend fun submit(form: LeaveForm, attachment: LeaveAttachment?): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Post,
            path = REQUESTS,
            configure = {
                multipart {
                    append("type", form.type.apiValue)
                    append("start_date", form.startDate)
                    append("end_date", form.endDate)
                    append("reason", form.reason.trim())
                    form.link.trim().takeIf { it.isNotEmpty() && attachment == null }?.let { append("link", it) }
                    if (attachment != null) appendFile("file", attachment.bytes, attachment.contentType, attachment.fileName)
                }
            },
            parse = { },
        )

    override suspend fun cancel(id: String): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Delete,
            path = "$REQUESTS/$id",
            configure = {},
            parse = { },
        )
}
