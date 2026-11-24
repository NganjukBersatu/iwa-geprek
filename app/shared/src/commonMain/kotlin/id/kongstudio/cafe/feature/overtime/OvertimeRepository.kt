package id.kongstudio.cafe.feature.overtime

import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult

internal interface OvertimeRepository {
    /** Riwayat lembur pengguna bulan ini, terjadwal dan dadakan, terbaru dulu. */
    suspend fun history(): ApiResult<List<OvertimeEntry>>

    suspend fun record(request: OvertimeRequest): WriteResult<Unit>
}
