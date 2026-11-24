package id.kongstudio.cafe.ui.component.usercard

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import coil3.compose.AsyncImage
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.component.appicon.AppIcon

/** Kartu identitas pengguna di puncak dashboard; [containerColor] dibuat transparan bila kartu berada di atas latar lain, dan [contentPadding] mengatur jarak isi dari tepi kartu. */
@Composable
fun UserCard(
    name: String,
    modifier: Modifier = Modifier,
    subtitle: String? = null,
    photoUrl: String? = null,
    tag: String? = null,
    containerColor: Color = AppTheme.colors.primary,
    contentPadding: PaddingValues = PaddingValues(AppTheme.spacing.lg),
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(AppTheme.shapes.card)
            .background(containerColor)
            .padding(contentPadding),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.md),
    ) {
        Box(
            modifier = Modifier
                .size(AppTheme.sizes.avatarLarge)
                .clip(AppTheme.shapes.pill)
                .background(colors.onPrimarySubtle),
            contentAlignment = Alignment.Center,
        ) {
            if (photoUrl != null) {
                AsyncImage(
                    model = photoUrl,
                    contentDescription = null,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.matchParentSize(),
                )
            } else {
                AppIcon(icon = AppIcons.UserCircle, tint = colors.onPrimary, size = AppTheme.sizes.iconXLarge)
            }
        }
        Column(modifier = Modifier.weight(1f)) {
            BasicText(
                text = name,
                style = AppTheme.typography.title.copy(color = colors.onPrimary),
            )
            if (subtitle != null) {
                BasicText(
                    text = subtitle,
                    style = AppTheme.typography.body.copy(color = colors.onPrimaryMuted),
                )
            }
            if (tag != null) {
                BasicText(
                    text = tag,
                    style = AppTheme.typography.label.copy(color = colors.content),
                    modifier = Modifier
                        .padding(top = spacing.xs)
                        .clip(AppTheme.shapes.pill)
                        .background(colors.surfaceAccent)
                        .padding(horizontal = spacing.md, vertical = spacing.xs),
                )
            }
        }
    }
}
