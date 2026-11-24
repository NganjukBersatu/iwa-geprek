package id.kongstudio.cafe.feature.performance

import id.kongstudio.cafe.core.network.ApiResult

internal interface PerformanceRepository {
    suspend fun load(range: PerformanceRange): ApiResult<Performance>
}
