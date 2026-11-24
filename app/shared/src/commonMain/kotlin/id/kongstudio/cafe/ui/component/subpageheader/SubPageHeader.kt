package id.kongstudio.cafe.ui.component.subpageheader

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

/** Tujuan kembali: label "Kembali ke ..." dan aksinya. */
class HeaderBack(val label: String, val onClick: () -> Unit)

/** Lebar judul mengikuti lebar isi halamannya supaya tombol kembali, judul, dan isi berbagi satu tepi kiri. */
enum class HeaderWidth {
    /** Isi halaman dibatasi lebar baca di tengah, seperti halaman aplikasi karyawan. */
    Content,

    /** Isi halaman selebar layar dengan jarak tepi halaman, seperti halaman turunan tablet. */
    Page,
}

/** Judul halaman turunan; bila [back] ada, panah berlabel tujuan tampil di atas judul, dan [trailing] (lencana, penghitung) mengalir di samping judul. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SubPageHeader(
    title: String,
    modifier: Modifier = Modifier,
    back: HeaderBack? = null,
    width: HeaderWidth = HeaderWidth.Content,
    trailing: (@Composable () -> Unit)? = null,
) {
    val spacing = AppTheme.spacing
    val column = when (width) {
        HeaderWidth.Content -> Modifier.widthIn(max = AppTheme.sizes.contentMaxWidth).fillMaxWidth().padding(horizontal = spacing.md)
        HeaderWidth.Page -> Modifier.fillMaxWidth().padding(horizontal = AppTheme.windowSize.pagePadding)
    }
    Box(modifier = modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
        // Jarak bawah menjaga isi yang digulir tidak menempel pada judul yang tetap di atas.
        Column(modifier = column.padding(bottom = spacing.sm)) {
            if (back != null) BackLink(label = back.label, onClick = back.onClick)
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(spacing.sm),
                verticalArrangement = Arrangement.spacedBy(spacing.xs),
                itemVerticalAlignment = Alignment.CenterVertically,
            ) {
                BasicText(text = title, style = AppTheme.typography.title.copy(color = AppTheme.colors.content))
                trailing?.invoke()
            }
        }
    }
}

/** Panah dan label tujuan sebagai satu tombol kembali yang selebar targetnya. */
@Composable
private fun BackLink(label: String, onClick: () -> Unit) {
    val spacing = AppTheme.spacing
    Row(
        modifier = Modifier
            .heightIn(min = spacing.touchTarget)
            .clip(AppTheme.shapes.pill)
            .clickable(role = Role.Button, onClick = onClick)
            .padding(end = spacing.md),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(spacing.xs),
    ) {
        AppIcon(icon = AppIcons.ChevronLeft, tint = AppTheme.colors.primary, size = AppTheme.sizes.iconLarge)
        BasicText(text = label, style = AppTheme.typography.label.copy(color = AppTheme.colors.primary))
    }
}
