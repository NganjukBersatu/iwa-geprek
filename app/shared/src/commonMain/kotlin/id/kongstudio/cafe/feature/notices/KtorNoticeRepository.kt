package id.kongstudio.cafe.feature.notices

import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import io.ktor.client.call.body
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.HttpMethod
import io.ktor.http.contentType

private const val BASE = "/v2/notices"

internal class KtorNoticeRepository(private val api: ApiCaller) : NoticeRepository {

    override suspend fun visible(): ApiResult<List<NoticeItem>> =
        api.read(BASE) { response -> response.body<List<NoticeDto>>().map { it.toModel() } }

    override suspend fun markRead(ids: List<String>): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Post,
            path = "$BASE/read",
            configure = {
                contentType(ContentType.Application.Json)
                setBody(ReadNoticesDto(ids))
            },
            parse = { },
        )
}
