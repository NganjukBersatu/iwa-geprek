package id.kongstudio.cafe.feature.leave

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.text.UiText
import id.kongstudio.cafe.core.text.resolve
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.leave_attachment
import id.kongstudio.cafe.resources.leave_attachment_pdf
import id.kongstudio.cafe.resources.leave_cancel_action
import id.kongstudio.cafe.resources.leave_cancel_confirm
import id.kongstudio.cafe.resources.leave_cancel_message
import id.kongstudio.cafe.resources.leave_cancel_title
import id.kongstudio.cafe.resources.leave_detail_date
import id.kongstudio.cafe.resources.leave_detail_decided_by
import id.kongstudio.cafe.resources.leave_detail_link
import id.kongstudio.cafe.resources.leave_detail_note
import id.kongstudio.cafe.resources.leave_detail_reason
import id.kongstudio.cafe.resources.leave_detail_status
import id.kongstudio.cafe.resources.leave_detail_title
import id.kongstudio.cafe.resources.leave_detail_type
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.detailrow.DetailRow
import id.kongstudio.cafe.ui.component.detaillist.DetailList
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.component.listcard.ListCard
import id.kongstudio.cafe.ui.component.photopair.PhotoItem
import id.kongstudio.cafe.ui.component.photopair.PhotoPair
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Detail satu pengajuan; yang masih menunggu bisa dibatalkan oleh pemohonnya. */
@Composable
internal fun LeaveDetailSheet(
    request: LeaveRequest,
    working: Boolean,
    error: UiText?,
    onCancel: () -> Unit,
    onDismiss: () -> Unit,
) {
    var confirming by remember { mutableStateOf(false) }
    val attachmentUrl = request.attachmentUrl
    val isPdf = attachmentUrl?.substringBefore('?')?.endsWith(".pdf", ignoreCase = true) == true

    val rows = buildList<@Composable () -> Unit> {
        add { DetailRow(stringResource(Res.string.leave_detail_type), value = leaveTypeLabel(request.type)) }
        add { DetailRow(stringResource(Res.string.leave_detail_date), value = leaveRangeLabel(request)) }
        add { DetailRow(stringResource(Res.string.leave_detail_reason), value = request.reason) }
        add {
            DetailRow(
                stringResource(Res.string.leave_detail_status),
                valueContent = { LeaveStatusBadge(request.status) },
            )
        }
        request.decidedBy?.let { name ->
            add { DetailRow(stringResource(Res.string.leave_detail_decided_by), value = name) }
        }
        request.managerNote?.let { note ->
            add { DetailRow(stringResource(Res.string.leave_detail_note), value = note) }
        }
        request.attachmentLink?.let { link ->
            add { DetailRow(stringResource(Res.string.leave_detail_link), value = link) }
        }
        if (isPdf) {
            add {
                DetailRow(
                    stringResource(Res.string.leave_attachment),
                    value = stringResource(Res.string.leave_attachment_pdf),
                )
            }
        }
    }

    AppBottomSheet(title = stringResource(Res.string.leave_detail_title), onDismiss = onDismiss) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
            DetailList(rows)
            if (attachmentUrl != null && !isPdf) {
                PhotoPair(
                    first = PhotoItem(attachmentUrl, stringResource(Res.string.leave_attachment)),
                    second = PhotoItem(null, ""),
                )
            }
            error?.let { InlineMessage(text = it.resolve()) }
            if (request.status == LeaveStatus.Pending) {
                PrimaryButton(
                    text = stringResource(Res.string.leave_cancel_action),
                    onClick = { confirming = true },
                    containerColor = AppTheme.colors.danger,
                    modifier = Modifier.padding(top = AppTheme.spacing.sm),
                    loading = working,
                )
            }
        }
    }

    if (confirming) {
        ConfirmSheet(
            title = stringResource(Res.string.leave_cancel_title),
            message = stringResource(Res.string.leave_cancel_message),
            confirmLabel = stringResource(Res.string.leave_cancel_confirm),
            onConfirm = {
                onCancel()
                confirming = false
            },
            onDismiss = { confirming = false },
            destructive = true,
            enabled = !working,
        )
    }
}
