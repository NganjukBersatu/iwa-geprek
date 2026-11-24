package id.kongstudio.cafe.ui.component.multichoiceflow

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.chip.AppChip
import id.kongstudio.cafe.ui.theme.AppTheme

/** Pilihan jamak dalam kisi berlebar sama: jumlah kolom dari ukuran layar, dan satu baris setinggi pilihan tertingginya. */
@Composable
fun MultiChoiceFlow(
    label: String,
    options: List<String>,
    selected: Set<Int>,
    onToggle: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = AppTheme.spacing
    val columns = AppTheme.windowSize.choiceColumns

    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(spacing.xs)) {
        BasicText(text = label, style = AppTheme.typography.label.copy(color = AppTheme.colors.content))
        Column(verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
            options.indices.chunked(columns).forEach { row ->
                Row(
                    modifier = Modifier.fillMaxWidth().height(IntrinsicSize.Min),
                    horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                ) {
                    row.forEach { index ->
                        AppChip(
                            label = options[index],
                            selected = index in selected,
                            onClick = { onToggle(index) },
                            shape = AppTheme.shapes.field,
                            modifier = Modifier.weight(1f).fillMaxHeight(),
                        )
                    }
                    // Baris terakhir yang tidak penuh tetap memakai lebar kolom yang sama.
                    repeat(columns - row.size) { Spacer(Modifier.weight(1f)) }
                }
            }
        }
    }
}
