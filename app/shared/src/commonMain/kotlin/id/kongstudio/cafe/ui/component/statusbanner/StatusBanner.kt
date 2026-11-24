package id.kongstudio.cafe.ui.component.statusbanner

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

enum class BannerTone { Info, Warning }

/** Baris keterangan keadaan di atas halaman, dengan satu aksi opsional di ujung kanan; [icon] menggantikan ikon bawaan nada bila keadaannya punya ikon sendiri, seperti offline. */
@Composable
fun StatusBanner(
    text: String,
    modifier: Modifier = Modifier,
    tone: BannerTone = BannerTone.Info,
    icon: ImageVector? = null,
    actionLabel: String? = null,
    onAction: (() -> Unit)? = null,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val container = if (tone == BannerTone.Warning) colors.warningContainer else colors.selected
    val content = if (tone == BannerTone.Warning) colors.warning else colors.primary

    Row(
        modifier = modifier
            .fillMaxWidth()
            .semantics { liveRegion = LiveRegionMode.Polite }
            .background(container)
            .padding(horizontal = spacing.lg, vertical = spacing.sm),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.md),
    ) {
        AppIcon(
            icon = icon ?: if (tone == BannerTone.Warning) AppIcons.Alert else AppIcons.Info,
            tint = content,
            size = AppTheme.sizes.iconSmall,
        )
        BasicText(
            text = text,
            style = AppTheme.typography.label.copy(color = content),
            modifier = Modifier.weight(1f),
        )
        if (actionLabel != null && onAction != null) {
            BasicText(
                text = actionLabel,
                style = AppTheme.typography.label.copy(color = content),
                modifier = Modifier
                    .clickable(role = Role.Button, onClick = onAction)
                    .padding(spacing.xs),
            )
        }
    }
}
