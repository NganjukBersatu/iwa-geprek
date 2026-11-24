package id.kongstudio.cafe.feature.performance

import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import io.ktor.client.call.body
import io.ktor.client.request.parameter

internal class KtorPerformanceRepository(private val v2Api: ApiCaller) : PerformanceRepository {
    override suspend fun load(range: PerformanceRange): ApiResult<Performance> =
        v2Api.read(
            path = "/v2/performance",
            configure = { parameter("range", range.key) },
        ) { it.body<PerformanceDto>().toModel() }
}
