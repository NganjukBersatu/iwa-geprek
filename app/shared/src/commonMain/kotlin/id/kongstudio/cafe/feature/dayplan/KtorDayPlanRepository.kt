package id.kongstudio.cafe.feature.dayplan

import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import io.ktor.client.call.body

private const val DAY_PLAN = "/v2/day-plan"

internal class KtorDayPlanRepository(private val api: ApiCaller) : DayPlanRepository {

    override suspend fun load(): ApiResult<DayPlan> =
        api.read(DAY_PLAN) { it.body<DayPlanDto>().toModel() }
}
