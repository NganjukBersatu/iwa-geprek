package id.kongstudio.cafe.ui.component.panelsurface

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import id.kongstudio.cafe.ui.theme.AppTheme

/** Permukaan kartu yang memenuhi panel samping, berbingkai tipis dan bersudut bulat. */
@Composable
fun PanelSurface(
    modifier: Modifier = Modifier,
    content: @Composable BoxScope.() -> Unit,
) {
    val colors = AppTheme.colors
    val shape = AppTheme.shapes.card
    Box(
        modifier = modifier
            .fillMaxSize()
            .padding(AppTheme.spacing.sm)
            .clip(shape)
            .background(colors.surface)
            .border(AppTheme.sizes.borderThin, colors.divider, shape),
        content = content,
    )
}
