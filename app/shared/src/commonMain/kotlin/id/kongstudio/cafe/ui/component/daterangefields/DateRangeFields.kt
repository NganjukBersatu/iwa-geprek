package id.kongstudio.cafe.ui.component.daterangefields

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.datefield.DateField
import id.kongstudio.cafe.ui.theme.AppTheme

/** Pasangan tanggal awal dan akhir ("YYYY-MM-DD"); rentang tidak pernah terbalik: memilih awal setelah akhir menggeser akhir, dan memilih akhir sebelum awal menggeser awal; sisi kosong (dengan [placeholder]) berarti terbuka. */
@Composable
internal fun DateRangeFields(
    from: String,
    to: String,
    today: String,
    fromLabel: String,
    toLabel: String,
    onChange: (from: String, to: String) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    sideBySide: Boolean = false,
    placeholder: String? = null,
) {
    val fromField = @Composable { fieldModifier: Modifier ->
        DateField(
            label = fromLabel,
            value = from,
            today = today,
            enabled = enabled,
            placeholder = placeholder,
            onValueChange = { onChange(it, if (to.isNotEmpty() && to < it) it else to) },
            modifier = fieldModifier,
        )
    }
    val toField = @Composable { fieldModifier: Modifier ->
        DateField(
            label = toLabel,
            value = to,
            today = today,
            enabled = enabled,
            placeholder = placeholder,
            onValueChange = { onChange(if (from.isNotEmpty() && from > it) it else from, it) },
            modifier = fieldModifier,
        )
    }

    if (sideBySide) {
        Row(modifier = modifier, horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
            fromField(Modifier.weight(1f))
            toField(Modifier.weight(1f))
        }
    } else {
        Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md)) {
            fromField(Modifier)
            toField(Modifier)
        }
    }
}
