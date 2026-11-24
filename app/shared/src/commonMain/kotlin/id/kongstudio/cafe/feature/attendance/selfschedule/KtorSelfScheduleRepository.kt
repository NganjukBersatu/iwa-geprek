package id.kongstudio.cafe.feature.attendance.selfschedule

import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import io.ktor.client.call.body
import io.ktor.client.request.parameter
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.HttpMethod
import io.ktor.http.contentType

private const val BASE = "/v2/attendance/self-schedule"

internal class KtorSelfScheduleRepository(private val api: ApiCaller) : SelfScheduleRepository {

    override suspend fun options(outletId: String?): ApiResult<SelfScheduleOptions> =
        api.read(
            path = "$BASE/options",
            configure = { outletId?.let { parameter("outlet_id", it) } },
        ) { it.body<SelfScheduleOptionsDto>().toModel() }

    override suspend fun create(request: SelfScheduleRequest): WriteResult<String> =
        api.write(
            method = HttpMethod.Post,
            path = BASE,
            configure = {
                contentType(ContentType.Application.Json)
                setBody(SelfScheduleRequestDto(request.outletId, request.roleId, request.shiftCodeId, request.reason))
            },
            parse = { it.body<CreatedScheduleDto>().id },
        )
}
