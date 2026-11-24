package id.kongstudio.cafe.ui.component.codebadge

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import id.kongstudio.cafe.ui.theme.AppTheme

/** Lencana kode (misalnya kode shift) dengan titik warna yang ditentukan pengguna. */
@Composable
fun CodeBadge(
    text: String,
    color: Color?,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    Row(
        modifier = modifier
            .clip(AppTheme.shapes.pill)
            .background(colors.selected)
            .padding(horizontal = spacing.md, vertical = spacing.xs),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.xs),
    ) {
        Box(
            modifier = Modifier
                .size(spacing.sm)
                .clip(AppTheme.shapes.pill)
                .background(color ?: colors.contentMuted),
        )
        BasicText(text = text, style = AppTheme.typography.label.copy(color = colors.content))
    }
}
