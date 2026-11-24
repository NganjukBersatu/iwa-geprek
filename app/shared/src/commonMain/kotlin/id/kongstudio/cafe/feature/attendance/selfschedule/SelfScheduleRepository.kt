package id.kongstudio.cafe.feature.attendance.selfschedule

import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult

internal interface SelfScheduleRepository {
    /** Cabang dan peran selalu ada; saran kode shift hanya bila [outletId] diisi. */
    suspend fun options(outletId: String?): ApiResult<SelfScheduleOptions>

    /** Menyimpan jadwal dan mengembalikan id-nya, yang lalu dipakai absen datang. */
    suspend fun create(request: SelfScheduleRequest): WriteResult<String>
}
