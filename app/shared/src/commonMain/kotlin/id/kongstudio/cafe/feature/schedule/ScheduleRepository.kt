package id.kongstudio.cafe.feature.schedule

import id.kongstudio.cafe.core.format.YearMonth
import id.kongstudio.cafe.core.network.ApiResult

internal interface ScheduleRepository {
    /** Jadwal dan hari libur seluruh staf cabang pada [month], urut tanggal, dengan nama cabangnya. */
    suspend fun load(month: YearMonth): ApiResult<ScheduleMonth>
}
