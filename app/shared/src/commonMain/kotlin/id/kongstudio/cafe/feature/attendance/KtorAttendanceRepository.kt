package id.kongstudio.cafe.feature.attendance

import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import id.kongstudio.cafe.core.network.appendFile
import id.kongstudio.cafe.core.network.multipart
import io.ktor.client.call.body
import io.ktor.client.request.forms.FormBuilder
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.HttpMethod
import io.ktor.http.contentType

private const val BASE = "/v2/attendance"
private const val PHOTO_MIME = "image/jpeg"
private const val LOCATION_INSIDE = "inside"
private const val LOCATION_OUTSIDE = "outside"

internal class KtorAttendanceRepository(private val api: ApiCaller) : AttendanceRepository {

    override suspend fun state(): ApiResult<AttendanceState> =
        api.read("$BASE/state") { it.body<AttendanceStateDto>().toModel() }

    override suspend fun clock(kind: ClockKind, request: ClockRequest): WriteResult<AttendanceRecord> =
        api.write(
            method = HttpMethod.Post,
            path = "$BASE/${if (kind == ClockKind.In) "clock-in" else "clock-out"}",
            configure = { multipart { fill(request) } },
            parse = { it.body<AttendanceDto>().toModel() },
        )

    override suspend fun acknowledge(ids: List<String>): WriteResult<Unit> =
        api.write(
            method = HttpMethod.Post,
            path = "$BASE/auto-close-notices/ack",
            configure = {
                contentType(ContentType.Application.Json)
                setBody(AcknowledgeDto(ids))
            },
            parse = { },
        )

    private fun FormBuilder.fill(request: ClockRequest) {
        request.scheduleId?.let { append("schedule_id", it) }
        append("latitude", request.fix.latitude.toString())
        append("longitude", request.fix.longitude.toString())
        append("accuracy", request.fix.accuracyMeters.toString())
        append("location_mode", if (request.outside) LOCATION_OUTSIDE else LOCATION_INSIDE)
        request.note?.let { append("location_note", it) }
        appendFile("photo", request.photo, PHOTO_MIME, "attendance.jpg")
    }
}
