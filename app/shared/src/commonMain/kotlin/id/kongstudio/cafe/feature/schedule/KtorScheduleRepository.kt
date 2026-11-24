package id.kongstudio.cafe.feature.schedule

import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.format.YearMonth
import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import io.ktor.client.call.body
import io.ktor.client.request.parameter

internal class KtorScheduleRepository(
    private val api: ApiCaller,
    private val userId: String,
) : ScheduleRepository {

    override suspend fun load(month: YearMonth): ApiResult<ScheduleMonth> =
        api.read(
            path = "/v2/schedule/month",
            configure = { parameter("month", DateTimeFormat.monthKey(month)) },
        ) { response -> response.body<MonthBoardDto>().toModel() }

    private fun MonthBoardDto.toModel(): ScheduleMonth {
        val codes = shiftCodes.map { it.toModel() }.associateBy { it.id }
        val items = assignments.map { shift ->
            val code = codes[shift.codeId]
            ScheduleItem(
                date = shift.date,
                code = code,
                roleName = shift.roleName,
                note = shift.note,
                off = code?.off == true,
                userId = shift.userId,
                userName = shift.userName,
                mine = shift.userId == userId,
            )
        } + daysOff.map { off ->
            ScheduleItem(
                date = off.date,
                code = codes[off.codeId],
                roleName = null,
                note = off.note,
                off = true,
                userId = off.userId,
                userName = off.userName,
                mine = off.userId == userId,
            )
        }
        return ScheduleMonth(items = items.sortedBy { it.date }, outletName = outletName)
    }
}
