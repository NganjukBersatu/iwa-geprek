package id.kongstudio.cafe.ui.component.iconpill

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme

/** Pil kecil berisi ikon dan teks, untuk menandai jenis atau jumlah, misalnya "2 pribadi". */
@Composable
fun IconPill(
    icon: ImageVector,
    text: String,
    modifier: Modifier = Modifier,
    containerColor: Color = AppTheme.colors.selected,
    contentColor: Color = AppTheme.colors.content,
) {
    val spacing = AppTheme.spacing

    Row(
        modifier = modifier
            .clip(AppTheme.shapes.pill)
            .background(containerColor)
            .padding(horizontal = spacing.md, vertical = spacing.xs),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.xs),
    ) {
        AppIcon(icon = icon, tint = contentColor, size = AppTheme.sizes.iconSmall)
        BasicText(text = text, style = AppTheme.typography.label.copy(color = contentColor))
    }
}
