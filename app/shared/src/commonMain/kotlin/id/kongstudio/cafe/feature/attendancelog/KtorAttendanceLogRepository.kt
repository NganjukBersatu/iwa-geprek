package id.kongstudio.cafe.feature.attendancelog

import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.YearMonth
import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import io.ktor.client.call.body
import io.ktor.client.request.parameter

internal class KtorAttendanceLogRepository(private val v2Api: ApiCaller) : AttendanceLogRepository {
    override suspend fun load(month: YearMonth?): ApiResult<AttendanceMonth> =
        v2Api.read(
            path = "/v2/attendance/summary",
            configure = { if (month != null) parameter("month", DateTimeFormat.monthKey(month)) },
        ) { it.body<AttendanceSummaryDto>().toModel() }
}
