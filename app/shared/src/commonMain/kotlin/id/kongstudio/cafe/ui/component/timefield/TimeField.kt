package id.kongstudio.cafe.ui.component.timefield

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.pickerfield.PickerField
import id.kongstudio.cafe.ui.component.systemtimepicker.SystemTimePicker
import id.kongstudio.cafe.ui.theme.icon.AppIcons

/** Isian jam berformat "HH:MM" yang tampil seperti kolom teks dan membuka pemilih jam bawaan sistem saat diketuk. */
@Composable
internal fun TimeField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
) {
    var open by remember { mutableStateOf(false) }

    PickerField(
        label = label,
        valueText = value,
        icon = AppIcons.Clock,
        onClick = { open = true },
        modifier = modifier,
        enabled = enabled,
    )

    if (open) {
        SystemTimePicker(initial = value, onPicked = onValueChange, onDismiss = { open = false })
    }
}
