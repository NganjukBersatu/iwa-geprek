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

/** Judul halaman dengan keterangan kecil di bawahnya dan, bila perlu, tombol atau lencana lewat [trailing]: di kanan pada layar lebar, di bawah judul pada HP supaya judul tidak terpotong. */
@Composable
fun PageTitle(
    title: String,
    modifier: Modifier = Modifier,
    subtitle: String? = null,
    trailing: (@Composable RowScope.() -> Unit)? = null,
) {
    val spacing = AppTheme.spacing
    val phone = AppTheme.windowSize.isPhone
    val heading: @Composable (Modifier) -> Unit = { headingModifier ->
        Column(modifier = headingModifier) {
            AppText(text = title, role = if (phone) TextRole.Title else TextRole.Headline)
            subtitle?.let { AppText(text = it, role = TextRole.Caption, color = AppTheme.colors.contentMuted) }
        }
    }
    if (phone) {
        Column(modifier = modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(spacing.sm)) {
            heading(Modifier.fillMaxWidth())
            trailing?.let { Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(spacing.sm), content = it) }
        }
        return
    }
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.md),
    ) {
        heading(Modifier.weight(1f))
        trailing?.invoke(this)
    }
}
