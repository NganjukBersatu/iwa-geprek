package id.kongstudio.cafe.ui.component.formsheet

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.inlinemessage.InlineMessage
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_cancel
import org.jetbrains.compose.resources.stringResource
import id.kongstudio.cafe.ui.theme.AppTheme

/**
 * Lembar formulir seragam: isian dari pemanggil ([fields]), pesan galat, dan tombol simpan, yang tidak bisa ditutup selama [submitting];
 * [loadingOnSubmit] menampilkan titik berdenyut di tombol simpan selama [submitting].
 */
@Composable
fun FormSheet(
    title: String,
    submitLabel: String,
    onSubmit: () -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier,
    submitting: Boolean = false,
    canSubmit: Boolean = true,
    error: String? = null,
    loadingOnSubmit: Boolean = false,
    /** Bila diisi, tombol simpan tidak dinonaktifkan karena [canSubmit] salah: mengetuknya menampilkan pesan ini di atas tombol. */
    invalidMessage: String? = null,
    fields: @Composable ColumnScope.() -> Unit,
) {
    var attempted by remember { mutableStateOf(false) }
    AppBottomSheet(title = title, onDismiss = onDismiss, dismissible = !submitting) {
        Column(
            modifier = modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
        ) {
            fields()
            error?.let { InlineMessage(text = it) }
            if (invalidMessage != null && attempted && !canSubmit) InlineMessage(text = invalidMessage)
            Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
                PrimaryButton(
                    text = stringResource(Res.string.common_cancel),
                    onClick = onDismiss,
                    enabled = !submitting,
                    containerColor = AppTheme.colors.selected,
                    contentColor = AppTheme.colors.primary,
                    modifier = Modifier.weight(1f),
                )
                PrimaryButton(
                    text = submitLabel,
                    onClick = { if (canSubmit || invalidMessage == null) onSubmit() else attempted = true },
                    enabled = (canSubmit || invalidMessage != null) && !submitting,
                    loading = loadingOnSubmit && submitting,
                    modifier = Modifier.weight(1f),
                )
            }
        }
    }
}
