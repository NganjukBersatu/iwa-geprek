package id.kongstudio.cafe.feature.batches

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
internal class BatchPageDto(val items: List<BatchDto> = emptyList()) {
    fun toModels() = items.map { it.toModel() }
}

@Serializable
internal class BatchDto(
    val id: String,
    val kind: String? = null,
    @SerialName("fill_mode") val fillMode: String? = null,
    val name: String,
    @SerialName("start_clock") val startClock: String,
    @SerialName("end_clock") val endClock: String,
    val completed: Boolean = false,
    @SerialName("run_id") val runId: String? = null,
    @SerialName("can_fix") val canFix: Boolean = false,
    @SerialName("can_cancel") val canCancel: Boolean = false,
    @SerialName("can_delete") val canDelete: Boolean = false,
    val items: List<BatchItemDto> = emptyList(),
) {
    fun toModel() = Batch(
        id = id,
        kind = batchKindOf(kind),
        eachFills = eachFillsOf(fillMode),
        name = name,
        startClock = startClock,
        endClock = endClock,
        completed = completed,
        items = items.map { it.toModel() },
        runId = runId,
        canFix = canFix,
        canCancel = canCancel,
        canDelete = canDelete,
    )
}

@Serializable
internal class StoredRunDto(val batch: BatchDto, val answers: List<StoredAnswerDto> = emptyList()) {
    fun toModel(runId: String) = StoredRun(
        runId = runId,
        batch = batch.toModel(),
        values = answers.mapNotNull { answer -> answer.value?.let { answer.itemId to it } }.toMap(),
        photoUrls = answers.mapNotNull { answer -> answer.photoUrl?.let { answer.itemId to it } }.toMap(),
    )
}

@Serializable
internal class StoredAnswerDto(
    @SerialName("item_id") val itemId: String,
    val value: String? = null,
    @SerialName("photo_url") val photoUrl: String? = null,
)

@Serializable
internal class BatchItemDto(
    val id: String,
    val label: String,
    val kind: String,
    val required: Boolean = true,
) {
    fun toModel() = BatchItem(
        id = id,
        label = label,
        kind = BatchItemKind.entries.firstOrNull { it.apiValue == kind } ?: BatchItemKind.Text,
        required = required,
    )
}

/** [photoIndex] menunjuk urutan foto di antara berkas yang diunggah bersama jawaban. */
@Serializable
internal class BatchAnswerDto(
    @SerialName("item_id") val itemId: String,
    val value: String? = null,
    @SerialName("photo_index") val photoIndex: Int? = null,
    @SerialName("keep_photo") val keepPhoto: Boolean = false,
)
