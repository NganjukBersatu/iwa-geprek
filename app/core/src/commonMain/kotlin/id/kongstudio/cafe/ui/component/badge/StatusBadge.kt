package id.kongstudio.cafe.ui.component.badge

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme

enum class BadgeTone { Positive, Warning, Danger, Neutral, Accent, Strong }

/** Lencana keadaan; [icon] opsional supaya keadaan tidak dibedakan oleh warna saja. */
@Composable
fun StatusBadge(
    text: String,
    tone: BadgeTone,
    modifier: Modifier = Modifier,
    icon: ImageVector? = null,
) {
    val colors = AppTheme.colors
    val (container, content) = when (tone) {
        BadgeTone.Positive -> colors.selected to colors.primary
        BadgeTone.Warning -> colors.warningContainer to colors.warning
        BadgeTone.Danger -> colors.dangerContainer to colors.onDangerContainer
        BadgeTone.Neutral -> colors.divider to colors.contentMuted
        BadgeTone.Accent -> colors.accent to colors.content
        // warna teks pekat, untuk penanda yang harus berbeda jelas dari Positive dan Accent tanpa keluar dari palet.
        BadgeTone.Strong -> colors.primary to colors.onPrimary
    }

    Row(
        modifier = modifier
            .clip(AppTheme.shapes.pill)
            .background(container)
            .padding(horizontal = AppTheme.spacing.sm, vertical = AppTheme.spacing.xs),
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (icon != null) AppIcon(icon = icon, tint = content, size = AppTheme.sizes.iconSmall)
        BasicText(text = text, style = AppTheme.typography.caption.copy(color = content, fontWeight = FontWeight.SemiBold))
    }
}
