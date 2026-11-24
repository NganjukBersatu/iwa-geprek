package id.kongstudio.cafe.ui.component.choicegroup

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.ui.component.chip.AppChip
import id.kongstudio.cafe.ui.theme.AppTheme

/** Pilihan tunggal dari beberapa opsi pendek, dengan label di atasnya; [icons] opsional, satu per opsi dengan urutan yang sama. */
@Composable
fun ChoiceGroup(
    label: String,
    options: List<String>,
    selectedIndex: Int?,
    onSelect: (Int) -> Unit,
    modifier: Modifier = Modifier,
    icons: List<ImageVector> = emptyList(),
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs),
    ) {
        BasicText(text = label, style = AppTheme.typography.label.copy(color = AppTheme.colors.content))
        Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
            options.forEachIndexed { index, option ->
                AppChip(label = option, selected = index == selectedIndex, onClick = { onSelect(index) }, icon = icons.getOrNull(index))
            }
        }
    }
}
