package id.kongstudio.cafe.ui.component.floatingpillbutton

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme

private val Elevation = 6.dp

/** Tombol aksi utama berbentuk pil yang melayang di atas isi layar, berisi ikon dan [label]; letakkan di pojok bawah. */
@Composable
fun FloatingPillButton(
    icon: ImageVector,
    label: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val shape = AppTheme.shapes.pill

    Row(
        modifier = modifier
            .shadow(Elevation, shape)
            .clip(shape)
            .background(colors.primary)
            .heightIn(min = spacing.touchTarget)
            .clickable(role = Role.Button, onClick = onClick)
            .padding(horizontal = spacing.lg),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.sm),
    ) {
        AppIcon(icon = icon, tint = colors.onPrimary, size = AppTheme.sizes.iconSmall)
        BasicText(text = label, style = AppTheme.typography.label.copy(color = colors.onPrimary))
    }
}
