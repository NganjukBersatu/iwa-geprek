package id.kongstudio.cafe.ui.component.choiceflow

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.chip.AppChip
import id.kongstudio.cafe.ui.theme.AppTheme

/** Pilihan tunggal dari banyak opsi: chip turun ke baris berikutnya, tidak terpotong di tepi layar. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ChoiceFlow(
    label: String,
    options: List<String>,
    selectedIndex: Int?,
    onSelect: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs)) {
        BasicText(text = label, style = AppTheme.typography.label.copy(color = AppTheme.colors.content))
        FlowRow(
            horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
            verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
        ) {
            options.forEachIndexed { index, option ->
                AppChip(label = option, selected = index == selectedIndex, onClick = { onSelect(index) })
            }
        }
    }
}
