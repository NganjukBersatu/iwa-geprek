package id.kongstudio.cafe.feature.attendancelog

import id.kongstudio.cafe.core.format.YearMonth
import id.kongstudio.cafe.core.network.ApiResult

internal interface AttendanceLogRepository {
    /** [month] null berarti bulan berjalan menurut server. */
    suspend fun load(month: YearMonth?): ApiResult<AttendanceMonth>
}
