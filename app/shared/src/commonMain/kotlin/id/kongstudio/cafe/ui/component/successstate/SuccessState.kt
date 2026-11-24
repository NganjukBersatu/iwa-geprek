package id.kongstudio.cafe.ui.component.successstate

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import id.kongstudio.cafe.ui.component.iconbadge.IconBadge
import id.kongstudio.cafe.ui.theme.AppTheme

/** Keadaan berhasil: ikon, judul, dan satu kalimat keterangan di tengah. */
@Composable
fun SuccessState(
    title: String,
    message: String,
    icon: ImageVector,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    Column(
        modifier = modifier.fillMaxWidth().padding(vertical = spacing.xl),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(spacing.md),
    ) {
        IconBadge(icon = icon)
        BasicText(
            text = title,
            style = AppTheme.typography.title.copy(color = colors.content, textAlign = TextAlign.Center),
        )
        BasicText(
            text = message,
            style = AppTheme.typography.body.copy(color = colors.contentMuted, textAlign = TextAlign.Center),
        )
    }
}
