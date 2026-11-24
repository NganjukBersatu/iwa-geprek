package id.kongstudio.cafe.ui.component.cardgrid

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.theme.AppTheme

private const val Columns = 2
private const val WideRowWeight = 0.4f

/** Kisi kartu dua kolom yang membagi tinggi tersedia rata ke semua baris; kartu sisa di baris terakhir melebar penuh dan hanya setinggi sebagian baris biasa. */
@Composable
fun <T> CardGrid(
    items: List<T>,
    modifier: Modifier = Modifier,
    card: @Composable (T) -> Unit,
) {
    val gap = AppTheme.spacing.md

    Box(modifier = modifier.fillMaxSize()) {
        Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(gap)) {
            items.chunked(Columns).forEach { row ->
                Row(
                    modifier = Modifier.fillMaxWidth().weight(if (row.size == Columns) 1f else WideRowWeight),
                    horizontalArrangement = Arrangement.spacedBy(gap),
                ) {
                    row.forEach { item ->
                        val width = if (row.size == Columns) Modifier.weight(1f) else Modifier.fillMaxWidth()
                        Box(modifier = width.fillMaxHeight()) { card(item) }
                    }
                }
            }
        }
    }
}
