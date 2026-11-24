package id.kongstudio.cafe.feature.cashier.cart

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.feature.cashier.LineNoteMaxLength
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.cashier_note
import id.kongstudio.cafe.resources.common_save
import id.kongstudio.cafe.ui.component.bottomsheet.AppBottomSheet
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

/** Catatan untuk satu baris pesanan, juga untuk menu tanpa varian yang langsung masuk keranjang; dikosongkan berarti catatannya dihapus. */
@Composable
internal fun LineNoteSheet(
    title: String,
    note: String,
    onDismiss: () -> Unit,
    onSave: (String) -> Unit,
) {
    var text by remember { mutableStateOf(note) }

    AppBottomSheet(title = title, onDismiss = onDismiss) {
        Column(verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
            AppTextField(
                value = text,
                onValueChange = { if (it.length <= LineNoteMaxLength) text = it },
                label = stringResource(Res.string.cashier_note),
            )
            PrimaryButton(
                text = stringResource(Res.string.common_save),
                onClick = { onSave(text) },
                modifier = Modifier.padding(bottom = AppTheme.spacing.sm),
            )
        }
    }
}
