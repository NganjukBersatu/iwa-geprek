package id.kongstudio.cafe.feature.dayplan

import id.kongstudio.cafe.core.network.ApiResult

internal interface DayPlanRepository {
    /** Jam kerja, lembur terjadwal, dan lembur dadakan milik karyawan yang berlaku hari ini. */
    suspend fun load(): ApiResult<DayPlan>
}
