package id.kongstudio.cafe.ui.component.listrow

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

/** Baris daftar: [leading] di kiri, judul dengan keterangan bertingkat, dan [trailing] di kanan; [opensDetail] menambah chevron penanda baris membuka rincian. */
@Composable
fun ListRow(
    title: String,
    modifier: Modifier = Modifier,
    detail: String? = null,
    caption: String? = null,
    footnote: String? = null,
    badge: (@Composable () -> Unit)? = null,
    leading: (@Composable () -> Unit)? = null,
    trailing: (@Composable () -> Unit)? = null,
    onClick: (() -> Unit)? = null,
    opensDetail: Boolean = false,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    Row(
        modifier = modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable(role = Role.Button, onClick = onClick) else Modifier)
            .padding(horizontal = spacing.lg, vertical = spacing.md),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.md),
    ) {
        leading?.invoke()
        Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(spacing.xs)) {
            BasicText(text = title, style = AppTheme.typography.label.copy(color = colors.content))
            if (detail != null) {
                BasicText(text = detail, style = AppTheme.typography.caption.copy(color = colors.content))
            }
            if (caption != null) {
                BasicText(text = caption, style = AppTheme.typography.caption.copy(color = colors.contentMuted))
            }
            if (footnote != null) {
                BasicText(text = footnote, style = AppTheme.typography.caption.copy(color = colors.contentMuted))
            }
            if (badge != null) {
                badge()
            }
        }
        trailing?.invoke()
        if (opensDetail && onClick != null) AppIcon(icon = AppIcons.ChevronRight, tint = colors.contentMuted, size = AppTheme.sizes.iconSmall)
    }
}
