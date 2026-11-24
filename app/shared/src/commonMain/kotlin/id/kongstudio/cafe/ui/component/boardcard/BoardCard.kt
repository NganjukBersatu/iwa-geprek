package id.kongstudio.cafe.ui.component.boardcard

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.unit.Dp
import id.kongstudio.cafe.ui.theme.AppTheme

/** Kartu satu pesanan atau item di papan: berbingkai tipis, dan saat [highlighted] berlatar terpilih dengan bingkai tebal. */
@Composable
fun BoardCard(
    modifier: Modifier = Modifier,
    highlighted: Boolean = false,
    shape: Shape = AppTheme.shapes.field,
    container: Color = AppTheme.colors.background,
    gap: Dp = AppTheme.spacing.sm,
    content: @Composable ColumnScope.() -> Unit,
) {
    val colors = AppTheme.colors
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(shape)
            .background(if (highlighted) colors.selected else container)
            .border(
                if (highlighted) AppTheme.sizes.borderThick else AppTheme.sizes.borderThin,
                if (highlighted) colors.primary else colors.divider,
                shape,
            )
            .padding(AppTheme.spacing.md),
        verticalArrangement = Arrangement.spacedBy(gap),
        content = content,
    )
}
