package id.kongstudio.cafe.ui.component.sidebaritem

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.component.appicon.AppIcon

// Untuk wadah berlatar primary; tanpa [icon] tampil sebagai butir anak yang lebih rendah dan saat terpilih berlatar warna aksen.
@Composable
fun SidebarItem(
    label: String,
    icon: ImageVector?,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    collapsed: Boolean = false,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    val child = icon == null
    val contentColor = when {
        selected && child -> colors.content
        selected -> colors.content
        else -> colors.background
    }
    val containerColor = when {
        selected && child -> colors.accent
        selected -> colors.surfaceAccent
        else -> Color.Transparent
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = if (child) spacing.compactTarget else spacing.touchTarget)
            .clip(AppTheme.shapes.field)
            .background(containerColor)
            .selectable(selected = selected, role = Role.Button, onClick = onClick)
            .padding(horizontal = spacing.md, vertical = spacing.sm),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = if (collapsed) Arrangement.Center else Arrangement.spacedBy(spacing.md),
    ) {
        if (icon != null) {
            AppIcon(icon = icon, tint = contentColor, size = AppTheme.sizes.icon, contentDescription = if (collapsed) label else null)
        } else {
            Box(modifier = Modifier.size(spacing.sm).clip(AppTheme.shapes.pill).background(contentColor))
        }
        if (!collapsed) {
            BasicText(
                text = label,
                style = AppTheme.typography.body.copy(
                    color = contentColor,
                    fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal,
                ),
                modifier = Modifier.weight(1f),
            )
        }
    }
}
