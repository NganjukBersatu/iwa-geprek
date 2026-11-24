package id.kongstudio.cafe.feature.sop

import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import io.ktor.client.call.body
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.HttpMethod
import io.ktor.http.contentType

internal class KtorSopRepository(private val api: ApiCaller) : SopRepository {

    override suspend fun list(): ApiResult<List<SopSummary>> =
        api.read("/v2/sop") { response -> response.body<List<SopSummaryDto>>().map { it.toModel() } }

    override suspend fun load(id: String): ApiResult<SopDocument> =
        api.read("/v2/sop/$id") { response -> response.body<SopDetailDto>().toModel() }

    override suspend fun reads(): ApiResult<Map<String, Int>> =
        api.read("/v2/sop/reads") { response -> response.body<List<SopReadDto>>().associate { it.sopId to it.version } }

    override suspend fun markRead(id: String, version: Int): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Put,
            path = "/v2/sop/$id/read",
            configure = {
                contentType(ContentType.Application.Json)
                setBody(SopReadInDto(version))
            },
            parse = { },
        )
}
