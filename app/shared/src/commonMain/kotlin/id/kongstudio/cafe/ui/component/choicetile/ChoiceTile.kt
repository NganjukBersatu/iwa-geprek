package id.kongstudio.cafe.ui.component.choicetile

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

private val TileMinHeight = 96.dp
private const val UnavailableAlpha = 0.8f

/** Kartu pilihan berikon dengan label dan lencana status, yang tetap bisa diketuk saat merah karena [available] false supaya pemanggil bisa menjelaskan sebabnya. */
@Composable
fun ChoiceTile(
    icon: ImageVector,
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    badge: String? = null,
    available: Boolean = true,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.field
    val (border, background) = when {
        !available -> colors.danger to colors.dangerContainer
        selected -> colors.accent to colors.selected
        else -> colors.outline to colors.surface
    }
    val iconTint = when {
        !available -> colors.contentMuted
        selected -> colors.primary
        else -> colors.contentMuted
    }
    // Keadaan terpilih memakai garis lebih tebal (rules 6.6.9), bukan hanya beda warna atau kepekatan latar, supaya tetap jelas dengan warna apa pun.
    val borderWidth = if (selected) AppTheme.sizes.borderThick else AppTheme.sizes.borderThin

    Column(
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = TileMinHeight)
            .alpha(if (available) 1f else UnavailableAlpha)
            .clip(shape)
            .background(background)
            .border(borderWidth, border, shape)
            .selectable(selected = selected, role = Role.RadioButton, onClick = onClick)
            .padding(spacing.md),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(spacing.xs, Alignment.CenterVertically),
    ) {
        AppIcon(icon = icon, tint = iconTint, size = AppTheme.sizes.icon)
        // Terpilih ditandai garis tebal dan centang, bukan warna saja (rules 6.4.12).
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(spacing.xs),
        ) {
            if (selected) AppIcon(icon = AppIcons.Check, tint = colors.primary, size = AppTheme.sizes.iconSmall)
            BasicText(
                text = label,
                style = AppTheme.typography.label.copy(color = colors.content, textAlign = TextAlign.Center),
                modifier = Modifier.weight(1f, fill = false),
            )
        }
        badge?.let { StatusBadge(text = it, tone = if (available) BadgeTone.Positive else BadgeTone.Danger) }
    }
}
