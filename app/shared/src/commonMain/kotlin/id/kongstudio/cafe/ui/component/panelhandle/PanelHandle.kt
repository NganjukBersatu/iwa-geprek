package id.kongstudio.cafe.ui.component.panelhandle

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

private const val RoundPercent = 50

/** Gagang di tepi panel geser berwarna warna lembut supaya terlihat di atas sidebar warna teks maupun halaman warna latar: [atStart] true bila panel di kiri, panah menunjuk arah geser berikutnya, dan [badge] tampil di atas gagang bila diisi. */
@Composable
fun PanelHandle(
    atStart: Boolean,
    hidden: Boolean,
    description: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    badge: String? = null,
) {
    val spacing = AppTheme.spacing
    val shape = if (atStart) {
        RoundedCornerShape(topEndPercent = RoundPercent, bottomEndPercent = RoundPercent)
    } else {
        RoundedCornerShape(topStartPercent = RoundPercent, bottomStartPercent = RoundPercent)
    }
    val pointsRight = atStart == hidden

    Box(modifier = modifier) {
        Box(
            modifier = Modifier
                .width(spacing.xl)
                .height(spacing.xxxl + spacing.xl)
                .clip(shape)
                .background(AppTheme.colors.surfaceAccent)
                .clickable(role = Role.Button, onClick = onClick),
            contentAlignment = Alignment.Center,
        ) {
            AppIcon(
                icon = if (pointsRight) AppIcons.ChevronRight else AppIcons.ChevronLeft,
                tint = AppTheme.colors.content,
                size = AppTheme.sizes.iconSmall,
                contentDescription = description,
            )
        }
        if (badge != null) {
            StatusBadge(
                text = badge,
                tone = BadgeTone.Warning,
                modifier = Modifier.align(Alignment.TopCenter).offset(y = -spacing.md),
            )
        }
    }
}
