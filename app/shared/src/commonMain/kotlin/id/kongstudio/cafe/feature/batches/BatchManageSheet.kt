package id.kongstudio.cafe.feature.batches

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.batch_cancel_action
import id.kongstudio.cafe.resources.batch_cancel_confirm
import id.kongstudio.cafe.resources.batch_cancel_message
import id.kongstudio.cafe.resources.batch_delete_action
import id.kongstudio.cafe.resources.batch_delete_confirm
import id.kongstudio.cafe.resources.batch_delete_message
import id.kongstudio.cafe.resources.batch_fix_action
import id.kongstudio.cafe.resources.batch_manage_hint
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.confirmsheet.ConfirmSheet
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

private enum class Pending { None, Fix, Cancel, Delete }

/** Yang bisa dilakukan pada pengisian yang sudah dikirim: perbaiki isinya, batalkan, atau hapus; tombol mengikuti hak dari server. */
@Composable
internal fun BatchManageSheet(
    batch: Batch,
    submitting: Boolean,
    error: String?,
    onFix: () -> Unit,
    onCancel: () -> Unit,
    onDelete: () -> Unit,
    onDismiss: () -> Unit,
) {
    val colors = AppTheme.colors
    var pending by remember { mutableStateOf(Pending.None) }
    var confirming by remember { mutableStateOf(Pending.None) }

    AppBottomSheet(title = batch.name, onDismiss = onDismiss, dismissible = !submitting) {
        Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
            AppText(text = stringResource(Res.string.batch_manage_hint), role = TextRole.Body, color = colors.contentMuted)
            error?.let { InlineMessage(text = it) }
            if (batch.canFix) {
                PrimaryButton(
                    text = stringResource(Res.string.batch_fix_action),
                    onClick = {
                        pending = Pending.Fix
                        onFix()
                    },
                    enabled = !submitting,
                    loading = submitting && pending == Pending.Fix,
                )
            }
            if (batch.canCancel) {
                PrimaryButton(
                    text = stringResource(Res.string.batch_cancel_action),
                    onClick = { confirming = Pending.Cancel },
                    enabled = !submitting,
                    loading = submitting && pending == Pending.Cancel,
                    containerColor = colors.selected,
                    contentColor = colors.primary,
                )
            }
            if (batch.canDelete) {
                PrimaryButton(
                    text = stringResource(Res.string.batch_delete_action),
                    onClick = { confirming = Pending.Delete },
                    enabled = !submitting,
                    loading = submitting && pending == Pending.Delete,
                    containerColor = colors.dangerContainer,
                    contentColor = colors.onDangerContainer,
                )
            }
        }
    }

    if (confirming == Pending.Cancel) {
        ConfirmSheet(
            title = stringResource(Res.string.batch_cancel_action),
            message = stringResource(Res.string.batch_cancel_message),
            confirmLabel = stringResource(Res.string.batch_cancel_confirm),
            onConfirm = {
                confirming = Pending.None
                pending = Pending.Cancel
                onCancel()
            },
            onDismiss = { confirming = Pending.None },
            enabled = !submitting,
        )
    }
    if (confirming == Pending.Delete) {
        ConfirmSheet(
            title = stringResource(Res.string.batch_delete_action),
            message = stringResource(Res.string.batch_delete_message),
            confirmLabel = stringResource(Res.string.batch_delete_confirm),
            onConfirm = {
                confirming = Pending.None
                pending = Pending.Delete
                onDelete()
            },
            onDismiss = { confirming = Pending.None },
            destructive = true,
            enabled = !submitting,
        )
    }
}
