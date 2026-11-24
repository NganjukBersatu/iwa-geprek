package id.kongstudio.cafe.ui.component.backbutton

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_back
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource
import id.kongstudio.cafe.ui.component.appicon.AppIcon

/** Tombol kembali berikon panah kiri dengan area ketuk penuh; dipakai di semua halaman turunan. */
@Composable
fun BackButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .size(AppTheme.spacing.touchTarget)
            .clip(AppTheme.shapes.pill)
            .clickable(role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        AppIcon(icon = AppIcons.ChevronLeft, tint = AppTheme.colors.primary, size = AppTheme.sizes.iconLarge, contentDescription = stringResource(Res.string.common_back))
    }
}
