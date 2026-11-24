package id.kongstudio.cafe.ui.component.sidebargroup

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

/** Kelompok menu di sidebar yang bisa dibuka-tutup, dengan [items] deretan SidebarItem dan [highlighted] menandai kelompok aktif saat tertutup. */
@Composable
fun SidebarGroup(
    label: String,
    icon: ImageVector,
    expanded: Boolean,
    onToggle: () -> Unit,
    modifier: Modifier = Modifier,
    highlighted: Boolean = false,
    items: @Composable ColumnScope.() -> Unit,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val emphasis = highlighted && !expanded

    Column(modifier = modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = spacing.touchTarget)
                .clip(AppTheme.shapes.field)
                .clickable(role = Role.Button, onClick = onToggle)
                .padding(horizontal = spacing.md, vertical = spacing.sm),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            AppIcon(icon = icon, tint = if (emphasis) colors.onPrimary else colors.background, size = AppTheme.sizes.icon)
            BasicText(
                text = label,
                style = AppTheme.typography.body.copy(
                    color = if (emphasis) colors.onPrimary else colors.background,
                    fontWeight = if (emphasis) FontWeight.Bold else FontWeight.Normal,
                ),
                modifier = Modifier.weight(1f),
            )
            // Hanya chevron yang menandai keadaan: grup terbuka berlingkaran hijau terang, grup tertutup polos.
            Box(
                modifier = Modifier
                    .size(AppTheme.sizes.icon)
                    .clip(AppTheme.shapes.pill)
                    .background(if (expanded) colors.surfaceAccent else Color.Transparent),
                contentAlignment = Alignment.Center,
            ) {
                AppIcon(
                    icon = if (expanded) AppIcons.ChevronUp else AppIcons.ChevronDown,
                    tint = if (expanded) colors.primary else colors.surfaceAccent,
                    size = AppTheme.sizes.iconSmall,
                )
            }
        }
        AnimatedVisibility(visible = expanded) {
            Column(
                modifier = Modifier.padding(start = spacing.lg),
                verticalArrangement = Arrangement.spacedBy(spacing.xs),
                content = items,
            )
        }
    }
}
