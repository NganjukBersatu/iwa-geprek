package id.kongstudio.cafe.ui.component.ratingstars

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

private const val StarCount = 5

/** Lima bintang terisi sesuai [stars] (0 sampai 5, boleh setengah); bintang kosong memakai warna pemisah. */
@Composable
fun RatingStars(stars: Float, description: String, modifier: Modifier = Modifier) {
    val colors = AppTheme.colors

    Row(
        modifier = modifier.semantics { contentDescription = description },
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs),
    ) {
        repeat(StarCount) { index ->
            val filled = (stars - index).coerceIn(0f, 1f)
            Box {
                AppIcon(icon = AppIcons.StarFilled, tint = colors.outline, size = AppTheme.sizes.iconLarge)
                if (filled > 0f) {
                    AppIcon(
                        icon = AppIcons.StarFilled,
                        tint = colors.accent,
                        size = AppTheme.sizes.iconLarge,
                        modifier = Modifier.drawWithContent {
                            clipRect(right = size.width * filled) { this@drawWithContent.drawContent() }
                        },
                    )
                }
            }
        }
    }
}
