package id.kongstudio.cafe.feature.notices

import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult

internal interface NoticeRepository {
    suspend fun visible(): ApiResult<List<NoticeItem>>

    suspend fun markRead(ids: List<String>): WriteResult<Unit>
}
