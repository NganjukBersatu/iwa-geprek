package id.kongstudio.cafe.ui.component.notice

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
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme

/** Keterangan keadaan kosong, memuat, atau gagal; satu kalimat di tengah, dengan [icon] dan [hint] langkah berikutnya bila keadaannya kosong yang perlu dijelaskan. */
@Composable
fun Notice(
    text: String,
    modifier: Modifier = Modifier,
    icon: ImageVector? = null,
    hint: String? = null,
) {
    val colors = AppTheme.colors
    if (icon == null && hint == null) {
        BasicText(
            text = text,
            style = AppTheme.typography.body.copy(color = colors.contentMuted, textAlign = TextAlign.Center),
            modifier = modifier.fillMaxWidth().padding(vertical = AppTheme.spacing.xl),
        )
        return
    }
    Column(
        modifier = modifier.fillMaxWidth().padding(vertical = AppTheme.spacing.xl),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
    ) {
        icon?.let { AppIcon(icon = it, tint = colors.contentMuted, size = AppTheme.sizes.iconXLarge) }
        BasicText(text = text, style = AppTheme.typography.title.copy(color = colors.content, textAlign = TextAlign.Center))
        hint?.let { BasicText(text = it, style = AppTheme.typography.body.copy(color = colors.contentMuted, textAlign = TextAlign.Center)) }
    }
}
