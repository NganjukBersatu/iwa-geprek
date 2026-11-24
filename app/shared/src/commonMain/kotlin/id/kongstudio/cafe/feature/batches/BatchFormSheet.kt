package id.kongstudio.cafe.feature.batches

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.batch_keep_photo
import id.kongstudio.cafe.resources.batch_missing
import id.kongstudio.cafe.resources.batch_optional_suffix
import id.kongstudio.cafe.resources.batch_submit
import id.kongstudio.cafe.resources.batch_toggle_ok
import id.kongstudio.cafe.resources.batch_toggle_problem
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.attachmentgallery.AttachmentGallery
import id.kongstudio.cafe.ui.component.attachmentgallery.RemoteAttachment
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.choiceflow.ChoiceFlow
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.mediafield.MediaKind
import id.kongstudio.cafe.ui.component.mediafield.PickedMedia
import id.kongstudio.cafe.ui.component.photofield.PhotoField
import id.kongstudio.cafe.ui.component.photopicker.PickedPhoto
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

private const val PhotoMime = "image/jpeg"
private const val PhotoName = "foto.jpg"

/** Lembar isi tugas outlet yang diselesaikan sekaligus, dengan item wajib yang kosong menahan penyelesaian dan menyebut item yang kurang. */
@Composable
internal fun BatchFormSheet(
    batch: Batch,
    submitting: Boolean,
    error: String?,
    onSubmit: (List<BatchAnswer>) -> Unit,
    onDismiss: () -> Unit,
    /** Jawaban dan foto yang sudah tersimpan saat form dipakai untuk memperbaiki pengisian. */
    initialValues: Map<String, String> = emptyMap(),
    keptPhotoUrls: Map<String, String> = emptyMap(),
    submitLabel: String = stringResource(Res.string.batch_submit),
) {
    val values = remember { mutableStateMapOf<String, String>().apply { putAll(initialValues) } }
    val photos = remember { mutableStateMapOf<String, PickedPhoto>() }
    var localError by remember { mutableStateOf<String?>(null) }
    val missingTemplate = stringResource(Res.string.batch_missing, "%s")

    AppBottomSheet(title = batch.name, onDismiss = onDismiss) {
        Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
            batch.items.forEach { item ->
                BatchItemField(
                    item = item,
                    value = values[item.id].orEmpty(),
                    photo = photos[item.id],
                    keptPhotoUrl = keptPhotoUrls[item.id],
                    enabled = !submitting,
                    onValueChange = {
                        values[item.id] = it
                        localError = null
                    },
                    onPhotoPicked = {
                        photos[item.id] = it
                        localError = null
                    },
                )
            }
            val shownError = error ?: localError
            if (shownError != null) InlineMessage(text = shownError)
            PrimaryButton(
                text = submitLabel,
                enabled = !submitting,
                loading = submitting,
                modifier = Modifier.fillMaxWidth(),
                onClick = {
                    val missing = batch.items.filter { item ->
                        item.required && isEmpty(item, values[item.id], photos[item.id], keptPhotoUrls[item.id])
                    }
                    if (missing.isEmpty()) {
                        onSubmit(answersOf(batch, values, photos, keptPhotoUrls))
                    } else {
                        localError = missingTemplate.replace("%s", missing.joinToString(", ") { it.label })
                    }
                },
            )
        }
    }
}

@Composable
private fun BatchItemField(
    item: BatchItem,
    value: String,
    photo: PickedPhoto?,
    keptPhotoUrl: String?,
    enabled: Boolean,
    onValueChange: (String) -> Unit,
    onPhotoPicked: (PickedPhoto) -> Unit,
) {
    val label = item.label + if (item.required) "" else stringResource(Res.string.batch_optional_suffix)

    when (item.kind) {
        BatchItemKind.Text -> AppTextField(value = value, onValueChange = onValueChange, label = label, enabled = enabled)

        BatchItemKind.Number -> AppTextField(
            value = value,
            onValueChange = onValueChange,
            label = label,
            enabled = enabled,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
        )

        BatchItemKind.Toggle -> ChoiceFlow(
            label = label,
            options = listOf(stringResource(Res.string.batch_toggle_ok), stringResource(Res.string.batch_toggle_problem)),
            selectedIndex = when (value) {
                ToggleOk -> 0
                ToggleProblem -> 1
                else -> null
            },
            onSelect = { onValueChange(if (it == 0) ToggleOk else ToggleProblem) },
        )

        BatchItemKind.Photo -> Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs)) {
            AppText(text = label, role = TextRole.Label)
            // Foto tersimpan tetap dipakai selama belum diganti foto baru.
            if (photo == null && keptPhotoUrl != null) {
                AttachmentGallery(attachments = listOf(RemoteAttachment(id = item.id, isVideo = false, url = keptPhotoUrl, removable = false)))
                AppText(text = stringResource(Res.string.batch_keep_photo), role = TextRole.Caption, color = AppTheme.colors.contentMuted)
            }
            PhotoField(photo = photo, onPicked = onPhotoPicked, enabled = enabled)
        }
    }
}

private fun isEmpty(item: BatchItem, value: String?, photo: PickedPhoto?, keptPhotoUrl: String?): Boolean =
    if (item.kind == BatchItemKind.Photo) photo == null && keptPhotoUrl == null else value.isNullOrBlank()

private fun answersOf(
    batch: Batch,
    values: Map<String, String>,
    photos: Map<String, PickedPhoto>,
    keptPhotoUrls: Map<String, String>,
): List<BatchAnswer> = batch.items.mapNotNull { item ->
    if (isEmpty(item, values[item.id], photos[item.id], keptPhotoUrls[item.id])) return@mapNotNull null
    if (item.kind == BatchItemKind.Photo) {
        val picked = photos[item.id] ?: return@mapNotNull BatchAnswer(item.id, value = null, photo = null, keepPhoto = true)
        BatchAnswer(item.id, value = null, photo = PickedMedia(MediaKind.Photo, picked.bytes, PhotoMime, PhotoName))
    } else {
        BatchAnswer(item.id, value = values.getValue(item.id).trim(), photo = null)
    }
}
