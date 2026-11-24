package id.kongstudio.cafe.ui.component.quantityfield

import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.textfield.AppTextField
import id.kongstudio.cafe.ui.theme.AppTheme

/**
 * Isian jumlah stok dengan [unit] menempel di dalam kolom, supaya angka yang diketik selalu terbaca bersama satuannya
 * (gr tidak tertukar dengan kg); papan ketik angka desimal.
 */
@Composable
fun QuantityField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    unit: String?,
    modifier: Modifier = Modifier,
    isError: Boolean = false,
    enabled: Boolean = true,
) {
    AppTextField(
        value = value,
        onValueChange = onValueChange,
        label = label,
        modifier = modifier,
        enabled = enabled,
        isError = isError,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
        trailing = unit?.takeIf { it.isNotBlank() }?.let { shown ->
            // Isian tidak memberi jarak kanan karena biasanya diisi tombol ikon; teks satuan butuh jaraknya sendiri.
            { AppText(text = shown, role = TextRole.Label, color = AppTheme.colors.contentMuted, modifier = Modifier.padding(end = AppTheme.spacing.md)) }
        },
    )
}
