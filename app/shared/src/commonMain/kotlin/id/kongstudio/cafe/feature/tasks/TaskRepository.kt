package id.kongstudio.cafe.feature.tasks

import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import id.kongstudio.cafe.ui.component.mediafield.PickedMedia

internal interface TaskRepository {
    /** Tugas yang cocok dengan [query]; tanpa tanggal server menampilkan bulan ini. */
    suspend fun load(query: TaskQuery): ApiResult<TaskPage>

    /** Pilihan formulir; [outletId] menentukan karyawan cabang mana yang ditawarkan. */
    suspend fun options(outletId: String?): ApiResult<TaskOptions>

    /** Isi pengisian tugas outlet atau tugas rutin yang ditindaklanjuti tugas ini. */
    suspend fun sourceRun(taskId: String): ApiResult<SourceRun>

    suspend fun create(task: NewTask): WriteResult<Unit>

    /** Mengubah judul, keterangan, dan batas waktu; [due] kosong membiarkan batas waktu seperti semula. */
    suspend fun update(taskId: String, title: String, description: String, due: String?): WriteResult<Unit>

    /** Menyelesaikan tugas; lampiran yang diunggah penyelesai menjadi buktinya. */
    suspend fun complete(taskId: String, note: String, media: List<PickedMedia>): WriteResult<Unit>

    /** Mengganti catatan selesai tugas yang sudah diselesaikan; teks kosong menghapus catatannya. */
    suspend fun fixCompletion(taskId: String, note: String): WriteResult<Unit>

    suspend fun addAttachments(taskId: String, media: List<PickedMedia>): WriteResult<Unit>

    suspend fun removeAttachment(taskId: String, attachmentId: String): WriteResult<Unit>

    suspend fun delete(taskId: String): WriteResult<Unit>
}
