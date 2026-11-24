package id.kongstudio.cafe.feature.attendance

import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult

internal interface AttendanceRepository {
    /** Apa yang boleh dilakukan karyawan sekarang beserta absen dan penugasan yang berlaku. */
    suspend fun state(): ApiResult<AttendanceState>

    suspend fun clock(kind: ClockKind, request: ClockRequest): WriteResult<AttendanceRecord>

    /** Menandai pemberitahuan penutupan otomatis sudah dilihat. */
    suspend fun acknowledge(ids: List<String>): WriteResult<Unit>
}
