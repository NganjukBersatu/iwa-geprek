package id.kongstudio.cafe.ui.component.sidebarsessionpanel

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

/** Panel sesi kas di dasar sidebar, berlatar warna latar supaya terpisah dari menu berwarna utama: menunjukkan status sesi dan membuka halaman sesi, tempat tombol buka dan tutup. */
@Composable
fun SidebarSessionPanel(
    title: String,
    status: String,
    onOpenPage: () -> Unit,
    modifier: Modifier = Modifier,
    selected: Boolean = false,
    collapsed: Boolean = false,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    Box(modifier = modifier.fillMaxWidth().padding(spacing.sm)) {
        if (collapsed) {
            Box(
                modifier = Modifier
                    .size(spacing.touchTarget)
                    .clip(AppTheme.shapes.field)
                    .background(colors.background)
                    .clickable(role = Role.Button, onClick = onOpenPage),
                contentAlignment = Alignment.Center,
            ) {
                AppIcon(icon = AppIcons.Clock, tint = colors.content, size = AppTheme.sizes.icon, contentDescription = title)
            }
            return@Box
        }

        Column(
            modifier = Modifier
                .fillMaxWidth()
                .clip(AppTheme.shapes.field)
                .background(colors.background)
                .padding(spacing.sm),
            verticalArrangement = Arrangement.spacedBy(spacing.sm),
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = spacing.touchTarget)
                    .clip(AppTheme.shapes.field)
                    .background(if (selected) colors.selected else Color.Transparent)
                    .clickable(role = Role.Button, onClick = onOpenPage)
                    .padding(horizontal = spacing.sm),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(spacing.md),
            ) {
                AppIcon(icon = AppIcons.Clock, tint = colors.content, size = AppTheme.sizes.icon)
                Column(modifier = Modifier.weight(1f)) {
                    BasicText(
                        text = title,
                        style = AppTheme.typography.body.copy(color = colors.content, fontWeight = FontWeight.Bold),
                    )
                    BasicText(
                        text = status,
                        style = AppTheme.typography.caption.copy(color = colors.contentMuted),
                    )
                }
                AppIcon(icon = AppIcons.ChevronRight, tint = colors.content, size = AppTheme.sizes.iconSmall)
            }

        }
    }
}


