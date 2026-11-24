package id.kongstudio.cafe.feature.dashboard

import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.feature.batches.Batch
import id.kongstudio.cafe.feature.batches.BatchPageDto
import io.ktor.client.call.body
import io.ktor.client.request.parameter

internal class KtorDashboardRepository(private val v2Api: ApiCaller) : DashboardRepository {

    override suspend fun loadProfile(): ApiResult<ProfileInfo> =
        v2Api.read("/v2/profile") { it.body<ProfileDto>().toModel() }

    override suspend fun loadSchedule(date: String): ApiResult<List<ScheduleEntry>> =
        v2Api.read(
            path = "/v2/schedule/mine",
            configure = { parameter("date", date) },
        ) { response -> response.body<List<ScheduleDto>>().map { it.toModel() } }

    override suspend fun loadTasks(): ApiResult<List<TaskDto>> =
        v2Api.read(
            path = "/v2/tasks/mine",
            configure = { parameter("size", 100) },
        ) { it.body<TaskPageDto>().items }

    override suspend fun loadBatches(): ApiResult<List<Batch>> =
        v2Api.read("/v2/batches/today") { it.body<BatchPageDto>().toModels() }

    override suspend fun loadAttendance(): ApiResult<AttendanceMonth> =
        v2Api.read("/v2/attendance/summary") { it.body<AttendanceSummaryDto>().toModel() }
}
