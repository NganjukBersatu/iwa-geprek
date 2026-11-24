package id.kongstudio.cafe.ui.component.datebadge

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.theme.AppTheme

/** Hari singkat di atas nomor tanggal, untuk baris daftar per hari. */
@Composable
fun DateBadge(
    weekday: String,
    day: String,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors

    Column(
        modifier = modifier.width(AppTheme.spacing.touchTarget),
        horizontalAlignment = Alignment.Start,
    ) {
        BasicText(text = weekday, style = AppTheme.typography.caption.copy(color = colors.contentMuted))
        BasicText(text = day, style = AppTheme.typography.button.copy(color = colors.content))
    }
}
