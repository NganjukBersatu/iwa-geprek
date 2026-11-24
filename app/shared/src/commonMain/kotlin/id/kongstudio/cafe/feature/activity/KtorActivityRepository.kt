package id.kongstudio.cafe.feature.activity

import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import io.ktor.client.call.body
import io.ktor.client.request.parameter

/** Jumlah aktivitas yang diminta sekaligus; batas atas yang diizinkan server. */
private const val PageLimit = 100

internal class KtorActivityRepository(private val v2Api: ApiCaller) : ActivityRepository {
    override suspend fun load(group: ActivityGroup): ApiResult<List<ActivityEvent>> =
        v2Api.read(
            path = "/v2/activity",
            configure = {
                parameter("limit", PageLimit)
                group.key?.let { parameter("group", it) }
            },
        ) { it.body<ActivityPageDto>().toModel() }
}
