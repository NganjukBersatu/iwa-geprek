package id.kongstudio.cafe.feature.tasks

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.format.longDateLabel
import id.kongstudio.cafe.core.format.whenLabel
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.tasks_attach_submit
import id.kongstudio.cafe.resources.tasks_complete_note
import id.kongstudio.cafe.resources.tasks_complete_submit
import id.kongstudio.cafe.resources.tasks_delete_action
import id.kongstudio.cafe.resources.tasks_delete_confirm
import id.kongstudio.cafe.resources.tasks_delete_message
import id.kongstudio.cafe.resources.tasks_detail_description
import id.kongstudio.cafe.resources.tasks_detail_done_at
import id.kongstudio.cafe.resources.tasks_detail_due
import id.kongstudio.cafe.resources.tasks_detail_follow_up
import id.kongstudio.cafe.resources.tasks_detail_follow_up_value
import id.kongstudio.cafe.resources.tasks_detail_giver
import id.kongstudio.cafe.resources.tasks_detail_name
import id.kongstudio.cafe.resources.tasks_detail_note
import id.kongstudio.cafe.resources.tasks_detail_outlet
import id.kongstudio.cafe.resources.tasks_detail_performer
import id.kongstudio.cafe.resources.tasks_detail_status
import id.kongstudio.cafe.resources.tasks_detail_title
import id.kongstudio.cafe.resources.tasks_proof_required
import id.kongstudio.cafe.resources.tasks_edit_action
import id.kongstudio.cafe.resources.tasks_filter_done
import id.kongstudio.cafe.resources.tasks_filter_pending
import id.kongstudio.cafe.resources.tasks_fix_note_submit
import id.kongstudio.cafe.resources.tasks_source_open
import id.kongstudio.cafe.ui.component.attachmentgallery.AttachmentGallery
import id.kongstudio.cafe.ui.component.attachmentgallery.RemoteAttachment
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.detailrow.DetailRow
import id.kongstudio.cafe.ui.component.detaillist.DetailList
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.mediafield.MediaField
import id.kongstudio.cafe.ui.component.mediafield.PickedMedia
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Detail satu tugas; baris yang tidak punya nilai tidak ditampilkan, dan tombol yang tampil mengikuti hak akses pemakai. */
@Composable
internal fun TaskDetailSheet(
    task: TaskItem,
    submitting: Boolean,
    submitError: UiText?,
    onComplete: (note: String, media: List<PickedMedia>) -> Unit,
    onAddAttachments: (media: List<PickedMedia>) -> Unit,
    onRemoveAttachment: (RemoteAttachment) -> Unit,
    onEdit: () -> Unit,
    onFixNote: (note: String) -> Unit,
    onOpenSource: () -> Unit,
    onDelete: () -> Unit,
    onDismiss: () -> Unit,
) {
    val colors = AppTheme.colors
    var note by remember { mutableStateOf("") }
    var fixedNote by remember(task.id, task.doneNote) { mutableStateOf(task.doneNote.orEmpty()) }
    var proof by remember { mutableStateOf<List<PickedMedia>>(emptyList()) }
    var proofMissing by remember { mutableStateOf(false) }
    var extra by remember { mutableStateOf<List<PickedMedia>>(emptyList()) }
    var confirmDelete by remember { mutableStateOf(false) }
    var deleting by remember { mutableStateOf(false) }

    val performer = task.assigneeName
    val rows = buildList<@Composable () -> Unit> {
        add { DetailRow(stringResource(Res.string.tasks_detail_name), value = task.title) }
        add {
            DetailRow(
                stringResource(Res.string.tasks_detail_status),
                valueContent = {
                    StatusBadge(
                        text = stringResource(
                            if (task.done) Res.string.tasks_filter_done else Res.string.tasks_filter_pending,
                        ),
                        tone = if (task.done) BadgeTone.Positive else BadgeTone.Warning,
                    )
                },
            )
        }
        task.outletName?.let { name -> add { DetailRow(stringResource(Res.string.tasks_detail_outlet), value = name) } }
        task.followUp?.let { source ->
            add {
                DetailRow(
                    stringResource(Res.string.tasks_detail_follow_up),
                    value = stringResource(Res.string.tasks_detail_follow_up_value, source.batchName, longDateLabel(source.day), source.number, source.total),
                )
            }
        }
        task.description?.let { text -> add { DetailRow(stringResource(Res.string.tasks_detail_description), value = text) } }
        task.creatorName?.takeIf { it != task.assigneeName }?.let { name ->
            add { DetailRow(stringResource(Res.string.tasks_detail_giver), value = name) }
        }
        performer?.let { name -> add { DetailRow(stringResource(Res.string.tasks_detail_performer), value = name) } }
        task.due?.let { due -> add { DetailRow(stringResource(Res.string.tasks_detail_due), value = whenLabel(due)) } }
        task.doneAt?.let { at -> add { DetailRow(stringResource(Res.string.tasks_detail_done_at), value = whenLabel(at)) } }
        task.doneNote?.let { text -> add { DetailRow(stringResource(Res.string.tasks_detail_note), value = text) } }
    }

    AppBottomSheet(
        title = stringResource(Res.string.tasks_detail_title),
        onDismiss = onDismiss,
        dismissible = !submitting,
    ) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
            DetailList(rows)
            if (task.followUp != null) {
                PrimaryButton(
                    text = stringResource(Res.string.tasks_source_open),
                    onClick = onOpenSource,
                    enabled = !submitting,
                    containerColor = colors.selected,
                    contentColor = colors.primary,
                )
            }
            AttachmentGallery(
                attachments = task.attachments,
                onRemove = onRemoveAttachment.takeIf { (task.canEdit || task.canFix) && !submitting },
            )

            val photos = task.attachments.count { !it.isVideo }
            val videos = task.attachments.count { it.isVideo }

            if (task.canComplete) {
                AppTextField(
                    value = note,
                    onValueChange = { note = it },
                    label = stringResource(Res.string.tasks_complete_note),
                    enabled = !submitting,
                )
                MediaField(
                    items = proof,
                    onChange = { proof = it },
                    enabled = !submitting,
                    existingPhotos = photos,
                    existingVideos = videos,
                )
            } else if (task.canEdit || task.canFix) {
                if (task.canFix) {
                    AppTextField(
                        value = fixedNote,
                        onValueChange = { fixedNote = it },
                        label = stringResource(Res.string.tasks_complete_note),
                        enabled = !submitting,
                    )
                    if (fixedNote.trim() != task.doneNote.orEmpty()) {
                        PrimaryButton(
                            text = stringResource(Res.string.tasks_fix_note_submit),
                            onClick = { onFixNote(fixedNote) },
                            enabled = !submitting,
                        )
                    }
                }
                MediaField(
                    items = extra,
                    onChange = { extra = it },
                    enabled = !submitting,
                    existingPhotos = photos,
                    existingVideos = videos,
                )
                if (extra.isNotEmpty()) {
                    PrimaryButton(
                        text = stringResource(Res.string.tasks_attach_submit),
                        onClick = {
                            onAddAttachments(extra)
                            extra = emptyList()
                        },
                        enabled = !submitting,
                    )
                }
            }

            submitError?.let { InlineMessage(text = it.resolve()) }

            if (task.canComplete) {
                // Tombol tetap aktif: bukti yang belum ada dijelaskan di atasnya, bukan membuat tombol abu tanpa alasan.
                if (proofMissing && proof.isEmpty()) InlineMessage(text = stringResource(Res.string.tasks_proof_required))
                PrimaryButton(
                    text = stringResource(Res.string.tasks_complete_submit),
                    onClick = {
                        if (proof.isEmpty()) {
                            proofMissing = true
                        } else {
                            deleting = false
                            onComplete(note, proof)
                        }
                    },
                    enabled = !submitting,
                    loading = submitting && !deleting,
                )
            }
            if (task.canEdit) {
                PrimaryButton(
                    text = stringResource(Res.string.tasks_edit_action),
                    onClick = onEdit,
                    enabled = !submitting,
                    containerColor = colors.selected,
                    contentColor = colors.primary,
                )
            }
            if (task.canDelete) {
                PrimaryButton(
                    text = stringResource(Res.string.tasks_delete_action),
                    onClick = { confirmDelete = true },
                    enabled = !submitting,
                    containerColor = colors.dangerContainer,
                    contentColor = colors.onDangerContainer,
                    loading = submitting && deleting,
                )
            }
        }
    }

    if (confirmDelete) {
        ConfirmSheet(
            title = stringResource(Res.string.tasks_delete_action),
            message = stringResource(Res.string.tasks_delete_message),
            confirmLabel = stringResource(Res.string.tasks_delete_confirm),
            onConfirm = {
                confirmDelete = false
                deleting = true
                onDelete()
            },
            onDismiss = { confirmDelete = false },
            destructive = true,
            enabled = !submitting,
        )
    }
}
