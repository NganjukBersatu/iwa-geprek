package id.kongstudio.cafe.feature.overtime

import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import io.ktor.client.call.body
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.HttpMethod
import io.ktor.http.contentType

private const val OVERTIME = "/v2/overtime"

internal class KtorOvertimeRepository(private val api: ApiCaller) : OvertimeRepository {

    override suspend fun history(): ApiResult<List<OvertimeEntry>> =
        api.read("$OVERTIME/mine") { response ->
            response.body<List<OvertimeEntryDto>>().map { it.toModel() }
        }

    override suspend fun record(request: OvertimeRequest): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Post,
            path = OVERTIME,
            configure = {
                contentType(ContentType.Application.Json)
                setBody(
                    UnplannedOvertimeDto(
                        startedAt = DateTimeFormat.wibIso(request.startDate, request.startTime),
                        endedAt = DateTimeFormat.wibIso(request.endDate, request.endTime),
                        note = request.note.trim(),
                    ),
                )
            },
            parse = { },
        )
}
