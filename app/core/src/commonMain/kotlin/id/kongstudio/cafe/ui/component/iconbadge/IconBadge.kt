package id.kongstudio.cafe.ui.component.iconbadge

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.component.appicon.AppIcon

enum class IconBadgeTone { Neutral, Warning }

/** Ikon di dalam lingkaran berlatar muda, untuk penanda jenis pada baris daftar; [tone] mewarnai lingkaran saat ikon juga menyatakan keadaan. */
@Composable
fun IconBadge(
    icon: ImageVector,
    modifier: Modifier = Modifier,
    tone: IconBadgeTone = IconBadgeTone.Neutral,
) {
    val colors = AppTheme.colors
    val (container, tint) = when (tone) {
        IconBadgeTone.Neutral -> colors.selected to colors.primary
        IconBadgeTone.Warning -> colors.warningContainer to colors.warning
    }

    Box(
        modifier = modifier
            .size(AppTheme.spacing.compactTarget)
            .clip(AppTheme.shapes.pill)
            .background(container),
        contentAlignment = Alignment.Center,
    ) {
        AppIcon(icon = icon, tint = tint, size = AppTheme.sizes.iconSmall)
    }
}
