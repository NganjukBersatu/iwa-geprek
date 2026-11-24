package id.kongstudio.cafe.ui.component.sidebarheader

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.appicon.AppIcon


// Dirancang untuk wadah berlatar primary.
@Composable
fun SidebarHeader(
    logo: Painter,
    logoDescription: String,
    title: String,
    subtitle: String,
    collapsed: Boolean,
    onToggleCollapsed: (() -> Unit)?,
    collapseDescription: String,
    expandDescription: String,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val typography = AppTheme.typography
    val spacing = AppTheme.spacing

    Column(modifier = modifier.fillMaxWidth()) {
        if (collapsed) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = spacing.md),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(spacing.xs),
            ) {
                BrandLogo(logo, logoDescription)
                onToggleCollapsed?.let { ToggleButton(AppIcons.ChevronRight, expandDescription, it) }
            }
        } else {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = spacing.md, vertical = spacing.md),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(spacing.md),
            ) {
                BrandLogo(logo, logoDescription)
                Column(modifier = Modifier.weight(1f)) {
                    BasicText(
                        text = title,
                        style = typography.body.copy(color = colors.onPrimary, fontWeight = FontWeight.Bold),
                    )
                    BasicText(
                        text = subtitle,
                        style = typography.label.copy(color = colors.surfaceAccent),
                    )
                }
                onToggleCollapsed?.let { ToggleButton(AppIcons.ChevronLeft, collapseDescription, it) }
            }
        }
        AppDivider()
    }
}

/** Logo merek di atas ubin warna latar supaya terbaca di latar warna utama; gambarnya tidak dipotong. */
@Composable
private fun BrandLogo(painter: Painter, description: String) {
    Box(
        modifier = Modifier
            .size(AppTheme.sizes.control)
            .clip(AppTheme.shapes.field)
            .background(AppTheme.colors.background)
            .padding(AppTheme.spacing.xs),
        contentAlignment = Alignment.Center,
    ) {
        Image(
            painter = painter,
            contentDescription = description,
            contentScale = ContentScale.Fit,
            modifier = Modifier.fillMaxSize(),
        )
    }
}

@Composable
private fun ToggleButton(icon: ImageVector, description: String, onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .size(AppTheme.spacing.touchTarget)
            .clip(AppTheme.shapes.pill)
            .clickable(role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        AppIcon(icon = icon, tint = AppTheme.colors.background, size = AppTheme.sizes.iconSmall, contentDescription = description)
    }
}
