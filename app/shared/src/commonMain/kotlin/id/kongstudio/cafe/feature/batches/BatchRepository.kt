package id.kongstudio.cafe.feature.batches

import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult

internal interface BatchRepository {
    /** Tugas outlet hari ini yang boleh dilihat orang ini, yaitu yang sudah absen dalam rentang waktunya. */
    suspend fun today(): ApiResult<List<Batch>>

    /** Menyelesaikan satu tugas outlet sekaligus; server menolak dengan keterangan bila ada item wajib yang kosong. */
    suspend fun complete(batchId: String, answers: List<BatchAnswer>): WriteResult<Batch>

    /** Pengisian beserta jawaban tersimpannya, untuk mengisi form perbaikan. */
    suspend fun stored(runId: String): ApiResult<StoredRun>

    /** Mengganti jawaban pengisian; isi lamanya tetap tercatat di riwayat admin. */
    suspend fun fix(runId: String, answers: List<BatchAnswer>): WriteResult<Batch>

    /** Tugas kembali belum diisi, dan isi lamanya tetap tercatat di riwayat admin. */
    suspend fun cancel(runId: String): WriteResult<Unit>

    /** Jawaban dan fotonya hilang permanen; admin hanya melihat siapa yang menghapus dan kapan. */
    suspend fun delete(runId: String): WriteResult<Unit>
}
