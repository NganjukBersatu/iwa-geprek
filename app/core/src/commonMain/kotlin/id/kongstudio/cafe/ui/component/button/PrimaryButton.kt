package id.kongstudio.cafe.ui.component.button

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.loadingdots.LoadingDots
import id.kongstudio.cafe.ui.theme.AppTheme

/**
 * Tombol utama; selama [loading] tombol tidak bisa diketuk dan isinya diganti titik berdenyut dengan ukuran tetap.
 * [icon] tampil di kiri label; [fullWidth] false untuk tombol selebar isinya, misalnya aksi di baris judul halaman.
 */
@Composable
fun PrimaryButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    containerColor: Color = AppTheme.colors.primary,
    contentColor: Color = AppTheme.colors.onPrimary,
    loading: Boolean = false,
    icon: ImageVector? = null,
    fullWidth: Boolean = true,
) {
    val spacing = AppTheme.spacing

    Box(
        modifier = modifier
            .then(if (fullWidth) Modifier.fillMaxWidth() else Modifier)
            .heightIn(min = spacing.touchTarget)
            .alpha(if (enabled || loading) 1f else AppTheme.colors.disabledAlpha)
            .clip(AppTheme.shapes.field)
            .background(containerColor)
            .clickable(enabled = enabled && !loading, role = Role.Button, onClick = onClick)
            .padding(horizontal = spacing.lg, vertical = spacing.md),
        contentAlignment = Alignment.Center,
    ) {
        Row(
            modifier = Modifier.alpha(if (loading) 0f else 1f),
            horizontalArrangement = Arrangement.spacedBy(spacing.sm),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (icon != null) AppIcon(icon = icon, tint = contentColor, size = AppTheme.sizes.iconSmall)
            BasicText(
                text = text,
                style = AppTheme.typography.button.copy(
                    color = contentColor,
                    textAlign = TextAlign.Center,
                ),
            )
        }
        if (loading) LoadingDots(color = contentColor)
    }
}
