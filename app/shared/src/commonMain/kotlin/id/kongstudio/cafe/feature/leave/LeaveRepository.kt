package id.kongstudio.cafe.feature.leave

import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult

internal interface LeaveRepository {
    /** Pengajuan milik pengguna, terbaru dulu. */
    suspend fun load(): ApiResult<List<LeaveRequest>>

    /** Mengajukan izin; [attachment] opsional dikirim bersama pengajuan, jadi gagal unggah tidak meninggalkan pengajuan. */
    suspend fun submit(form: LeaveForm, attachment: LeaveAttachment?): WriteResult<Unit>

    suspend fun cancel(id: String): WriteResult<Unit>
}
