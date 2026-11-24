package id.kongstudio.cafe.ui.component.sectiontitle

import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.theme.AppTheme

/** Judul bagian halaman di atas sekelompok isi. */
@Composable
fun SectionTitle(
    text: String,
    modifier: Modifier = Modifier,
    padded: Boolean = true,
) {
    BasicText(
        text = text,
        style = AppTheme.typography.label.copy(color = AppTheme.colors.contentMuted),
        modifier = if (padded) {
            modifier.padding(top = AppTheme.spacing.xl, bottom = AppTheme.spacing.sm)
        } else {
            modifier
        },
    )
}
