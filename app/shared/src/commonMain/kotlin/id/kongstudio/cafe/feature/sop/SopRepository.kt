package id.kongstudio.cafe.feature.sop

import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult

internal interface SopRepository {
    /** SOP yang tampil untuk karyawan, urut sesuai pengaturan admin. */
    suspend fun list(): ApiResult<List<SopSummary>>

    suspend fun load(id: String): ApiResult<SopDocument>

    /** Versi tiap SOP yang terakhir diselesaikan karyawan ini sampai slide terakhir, dicatat di server. */
    suspend fun reads(): ApiResult<Map<String, Int>>

    suspend fun markRead(id: String, version: Int): WriteResult<Unit>
}
