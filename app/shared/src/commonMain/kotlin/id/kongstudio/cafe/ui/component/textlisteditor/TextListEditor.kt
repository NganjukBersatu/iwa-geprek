package id.kongstudio.cafe.ui.component.textlisteditor

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.secondarybutton.SecondaryButton
import id.kongstudio.cafe.ui.component.iconbutton.AppIconButton
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

/** Daftar isian teks yang bisa ditambah dan dihapus, dengan perubahan dilaporkan per indeks supaya data pendamping (misalnya id) tetap sejajar. */
@Composable
fun TextListEditor(
    label: String,
    values: List<String>,
    onChange: (index: Int, value: String) -> Unit,
    onAdd: () -> Unit,
    onRemove: (index: Int) -> Unit,
    addLabel: String,
    removeDescription: String,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
) {
    Column(modifier = modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
        BasicText(text = label, style = AppTheme.typography.label.copy(color = AppTheme.colors.content))
        values.forEachIndexed { index, value ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.Bottom,
                horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
            ) {
                AppTextField(
                    value = value,
                    onValueChange = { onChange(index, it) },
                    label = "",
                    enabled = enabled,
                    modifier = Modifier.weight(1f),
                )
                AppIconButton(
                    icon = AppIcons.Close,
                    contentDescription = removeDescription,
                    onClick = { onRemove(index) },
                )
            }
        }
        SecondaryButton(text = addLabel, onClick = onAdd, enabled = enabled)
    }
}
