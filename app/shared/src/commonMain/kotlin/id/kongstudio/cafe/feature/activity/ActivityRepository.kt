package id.kongstudio.cafe.feature.activity

import id.kongstudio.cafe.core.network.ApiResult

internal interface ActivityRepository {
    /** Aktivitas terbaru lebih dulu; [group] membatasi satu jenis. */
    suspend fun load(group: ActivityGroup): ApiResult<List<ActivityEvent>>
}
