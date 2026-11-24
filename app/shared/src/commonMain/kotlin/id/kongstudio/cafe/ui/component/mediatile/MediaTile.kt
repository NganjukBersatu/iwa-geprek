package id.kongstudio.cafe.ui.component.mediatile

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.media_remove
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Kotak pratinjau satu lampiran: [onClick] membukanya dan tombol hapus di sudut tampil bila [onRemove] diberikan. */
@Composable
fun MediaTile(
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
    onRemove: (() -> Unit)? = null,
    removeEnabled: Boolean = true,
    content: @Composable BoxScope.() -> Unit,
) {
    val colors = AppTheme.colors
    val shape = AppTheme.shapes.field

    Box(
        modifier = modifier
            .size(AppTheme.sizes.thumbnail)
            .clip(shape)
            .background(colors.selected)
            .border(AppTheme.sizes.borderThin, colors.divider, shape)
            .then(if (onClick != null) Modifier.clickable(role = Role.Button, onClick = onClick) else Modifier),
        contentAlignment = Alignment.Center,
    ) {
        content()
        if (onRemove != null) {
            Box(
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(AppTheme.spacing.xs)
                    .size(AppTheme.sizes.controlSmall)
                    .clip(AppTheme.shapes.pill)
                    .background(colors.primary)
                    .clickable(enabled = removeEnabled, role = Role.Button, onClick = onRemove),
                contentAlignment = Alignment.Center,
            ) {
                AppIcon(
                    icon = AppIcons.Close,
                    tint = colors.onPrimary,
                    size = AppTheme.sizes.iconSmall,
                    contentDescription = stringResource(Res.string.media_remove),
                )
            }
        }
    }
}
