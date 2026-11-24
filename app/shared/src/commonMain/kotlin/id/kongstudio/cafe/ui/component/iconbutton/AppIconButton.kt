package id.kongstudio.cafe.ui.component.iconbutton

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.component.appicon.AppIcon

/** Tombol satu ikon dengan target sentuh penuh, dengan [badge] (misalnya jumlah item) tampil pekat di sudut kanan atas bila diisi; [containerColor] mengisi tombol menjadi lingkaran. */
@Composable
fun AppIconButton(
    icon: ImageVector,
    contentDescription: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    tint: Color = AppTheme.colors.content,
    badge: String? = null,
    containerColor: Color = Color.Transparent,
    badgeColor: Color = AppTheme.colors.primary,
    onBadgeColor: Color = AppTheme.colors.onPrimary,
) {
    val spacing = AppTheme.spacing

    Box(
        modifier = modifier
            .size(spacing.touchTarget)
            .background(containerColor, AppTheme.shapes.pill)
            .clickable(role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        AppIcon(icon = icon, tint = tint, size = AppTheme.sizes.icon, contentDescription = contentDescription)
        if (badge != null) {
            BasicText(
                text = badge,
                style = AppTheme.typography.label.copy(color = onBadgeColor),
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .offset(x = spacing.xs, y = -spacing.xs)
                    .clip(AppTheme.shapes.pill)
                    .background(badgeColor)
                    .padding(horizontal = spacing.sm, vertical = spacing.xs),
            )
        }
    }
}
