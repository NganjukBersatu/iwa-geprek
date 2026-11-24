package id.kongstudio.cafe.ui.component.centeredstat

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.theme.AppTheme

/** Ikon, label, angka, dan keterangan opsional yang bertumpuk dan rata tengah; dipakai di dalam kartu. */
@Composable
fun CenteredStat(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    icon: ImageVector? = null,
    caption: String? = null,
    valueColor: Color = AppTheme.colors.content,
) {
    val colors = AppTheme.colors

    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs),
    ) {
        if (icon != null) IconBadge(icon)
        AppText(text = label, role = TextRole.Caption, color = colors.contentMuted, textAlign = TextAlign.Center)
        AppText(text = value, role = TextRole.Title, color = valueColor, textAlign = TextAlign.Center, maxLines = 1)
        if (caption != null) {
            AppText(
                text = caption,
                role = TextRole.Caption,
                color = colors.contentMuted,
                textAlign = TextAlign.Center,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}
