package id.kongstudio.cafe.ui.component.confirmsheet

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_cancel
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Konfirmasi tindakan yang tidak bisa diurungkan: pesan, tombol lanjut, dan tombol batal. */
@Composable
fun ConfirmSheet(
    title: String,
    message: String,
    confirmLabel: String,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
    destructive: Boolean = false,
    enabled: Boolean = true,
    confirmEnabled: Boolean = true,
    dismissLabel: String = stringResource(Res.string.common_cancel),
    notice: @Composable () -> Unit = {},
) {
    val colors = AppTheme.colors

    AppBottomSheet(title = title, onDismiss = onDismiss, dismissible = enabled) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.lg),
        ) {
            BasicText(text = message, style = AppTheme.typography.body.copy(color = colors.content))
            notice()
            Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
                PrimaryButton(
                    text = dismissLabel,
                    onClick = onDismiss,
                    enabled = enabled,
                    containerColor = colors.selected,
                    contentColor = colors.primary,
                    modifier = Modifier.weight(1f),
                )
                PrimaryButton(
                    text = confirmLabel,
                    onClick = onConfirm,
                    enabled = enabled && confirmEnabled,
                    containerColor = if (destructive) colors.danger else colors.primary,
                    modifier = Modifier.weight(1f),
                )
            }
        }
    }
}
