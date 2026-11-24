package id.kongstudio.cafe.feature.batches

import id.kongstudio.cafe.ui.component.mediafield.PickedMedia

internal const val ToggleOk = "ok"
internal const val ToggleProblem = "problem"

/** Jenis isian satu item tugas outlet; nilainya sama dengan yang dipakai server. */
internal enum class BatchItemKind(val apiValue: String) {
    Text("text"),
    Number("number"),
    Photo("photo"),
    Toggle("toggle"),
}

internal class BatchItem(
    val id: String,
    val label: String,
    val kind: BatchItemKind,
    val required: Boolean,
)

/** Tugas outlet untuk siapa pun yang hadir di cabang, tugas rutin hanya untuk yang dijadwalkan di kode shiftnya. */
internal enum class BatchKind(val apiValue: String) {
    Outlet("outlet"),
    Routine("routine"),
}

private const val FillEach = "each"

/** Tugas rutin yang rentang waktunya ditentukan admin; [completed] berarti sudah diisi hari ini, oleh orang ini sendiri bila [eachFills]. */
internal class Batch(
    val id: String,
    val kind: BatchKind,
    val eachFills: Boolean,
    val name: String,
    val startClock: String,
    val endClock: String,
    val completed: Boolean,
    val items: List<BatchItem>,
    /** Pengisian hari ini yang berlaku bagi orang ini; null selama belum diisi. */
    val runId: String? = null,
    val canFix: Boolean = false,
    val canCancel: Boolean = false,
    val canDelete: Boolean = false,
) {
    val manageable: Boolean get() = runId != null && (canFix || canCancel || canDelete)

    val rangeLabel: String get() = "$startClock–$endClock"
}

/** Jenis dan cara isi dari nilai server; nilai yang tidak dikenal dibaca sebagai tugas outlet yang cukup diisi satu orang, seperti server lama. */
internal fun batchKindOf(apiValue: String?): BatchKind = BatchKind.entries.firstOrNull { it.apiValue == apiValue } ?: BatchKind.Outlet

internal fun eachFillsOf(apiValue: String?): Boolean = apiValue == FillEach

/** Jawaban satu item; [value] untuk teks, angka, dan pilihan Oke atau Bermasalah, [photo] untuk foto. */
internal class BatchAnswer(val itemId: String, val value: String?, val photo: PickedMedia?, val keepPhoto: Boolean = false)

/** Pengisian yang akan diperbaiki: [values] jawaban tersimpan per isian, [photoUrls] foto tersimpan per isian foto. */
internal class StoredRun(val runId: String, val batch: Batch, val values: Map<String, String>, val photoUrls: Map<String, String>)
