package id.kongstudio.cafe.feature.dashboard

import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.feature.batches.Batch

internal interface DashboardRepository {
    suspend fun loadProfile(): ApiResult<ProfileInfo>

    /** Penugasan pengguna pada tanggal [date] (YYYY-MM-DD). */
    suspend fun loadSchedule(date: String): ApiResult<List<ScheduleEntry>>

    suspend fun loadTasks(): ApiResult<List<TaskDto>>

    /** Tugas outlet hari ini untuk orang ini. */
    suspend fun loadBatches(): ApiResult<List<Batch>>

    /** Ringkasan bulan berjalan menurut server. */
    suspend fun loadAttendance(): ApiResult<AttendanceMonth>
}
