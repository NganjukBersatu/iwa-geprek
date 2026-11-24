package id.kongstudio.cafe.ui.component.pagetitle

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.theme.AppTheme

/** Judul halaman dengan keterangan kecil di bawahnya dan, bila perlu, tombol atau lencana di kanan lewat [trailing]. */
@Composable
fun PageTitle(
    title: String,
    modifier: Modifier = Modifier,
    subtitle: String? = null,
    trailing: (@Composable RowScope.() -> Unit)? = null,
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
    ) {
        Column(modifier = Modifier.weight(1f)) {
            AppText(text = title, role = TextRole.Headline)
            subtitle?.let { AppText(text = it, role = TextRole.Caption, color = AppTheme.colors.contentMuted) }
        }
        trailing?.invoke(this)
    }
}
