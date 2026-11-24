package id.kongstudio.cafe.feature.tasks

import id.kongstudio.cafe.core.format.WibStamp
import id.kongstudio.cafe.ui.component.attachmentgallery.RemoteAttachment
import id.kongstudio.cafe.ui.component.mediafield.PickedMedia

internal enum class TaskFilter(val apiValue: String) {
    Pending("belum"),
    Done("selesai"),
}

/** Rentang tanggal daftar tugas; "bulan ini" tidak mengirim tanggal sehingga server memakai bawaannya. */
internal enum class TaskPeriod { ThisMonth, Today, Week, Custom }

/** Semua yang menyempitkan daftar tugas; [page] berbasis nol, tanggal "YYYY-MM-DD" dan kosong berarti bawaan server. */
internal class TaskQuery(
    val filter: TaskFilter,
    val dateFrom: String?,
    val dateTo: String?,
    val outletId: String?,
    val search: String,
    val assigneeId: String?,
    val page: Int,
)

internal class TaskItem(
    val id: String,
    val title: String,
    val description: String?,
    val outletName: String?,
    /** Pemberi tugas; null bila akunnya sudah tidak ada. */
    val creatorName: String?,
    val assigneeName: String?,
    val due: WibStamp?,
    val done: Boolean,
    val doneNote: String?,
    val doneAt: WibStamp?,
    val attachments: List<RemoteAttachment>,
    /** Terisi bila tugas ini menindaklanjuti satu pengisian tugas outlet atau tugas rutin. */
    val followUp: TaskFollowUp?,
    /** Diberikan kepada orang yang membuka daftar. */
    val mine: Boolean,
    val canEdit: Boolean,
    val canComplete: Boolean,
    /** Tugas sudah selesai dan orang ini boleh membenahi catatan serta buktinya. */
    val canFix: Boolean,
    val canDelete: Boolean,
)

/** Pengisian yang ditindaklanjuti ([day] "YYYY-MM-DD") dan urutan tugas ini di antara semua tindak lanjutnya. */
internal class TaskFollowUp(val batchName: String, val day: String, val number: Int, val total: Int)

/** Isi pengisian yang ditindaklanjuti: siapa mengisi, kapan, dan jawabannya. */
internal class SourceRun(
    val batchName: String,
    val day: String,
    val outletName: String,
    val completedBy: String?,
    val completedAt: WibStamp?,
    val problems: Int,
    val answers: List<SourceAnswer>,
)

/** Jawaban satu isian; [photoUrl] hanya terisi untuk isian foto. */
internal class SourceAnswer(val label: String, val kind: String, val value: String?, val photoUrl: String?)

internal class TaskPage(
    val items: List<TaskItem>,
    val total: Int,
)

internal class TaskPerson(val id: String, val name: String)

internal class TaskOutlet(val id: String, val name: String)

/** Pilihan untuk formulir tugas: cabang yang boleh dipilih dan karyawan yang boleh diberi tugas. */
internal class TaskOptions(
    val outlets: List<TaskOutlet>,
    val assignees: List<TaskPerson>,
    val canManage: Boolean,
)

/** Isi formulir tugas baru; [due] sudah berformat ISO dengan zona waktu, atau null bila tanpa batas waktu. */
internal class NewTask(
    val title: String,
    val description: String,
    val assigneeId: String?,
    val due: String?,
    val complete: Boolean,
    val media: List<PickedMedia>,
)

internal const val TaskPageSize = 10
