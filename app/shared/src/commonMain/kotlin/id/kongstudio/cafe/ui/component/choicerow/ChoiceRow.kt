package id.kongstudio.cafe.ui.component.choicerow

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.chip.AppChip
import id.kongstudio.cafe.ui.theme.AppTheme

/** Pilihan tunggal dalam satu baris di semua lebar layar; bila tidak muat, baris digeser ke samping, tidak turun. */
@Composable
fun ChoiceRow(
    label: String,
    options: List<String>,
    selectedIndex: Int?,
    onSelect: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs)) {
        BasicText(text = label, style = AppTheme.typography.label.copy(color = AppTheme.colors.content))
        Row(
            modifier = Modifier.horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
        ) {
            options.forEachIndexed { index, option ->
                AppChip(label = option, selected = index == selectedIndex, onClick = { onSelect(index) })
            }
        }
    }
}
