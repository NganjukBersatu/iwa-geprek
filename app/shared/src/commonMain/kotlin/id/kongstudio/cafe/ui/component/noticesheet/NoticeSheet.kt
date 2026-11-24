package id.kongstudio.cafe.ui.component.noticesheet

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import id.kongstudio.cafe.ui.component.appdialog.AppDialog
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.divider.AppDivider
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme

/** Satu baris pengumuman: kalimat utama, keterangan waktunya, dan ikon penanda bila ada. */
class NoticeSheetItem(val title: String, val caption: String?, val icon: ImageVector? = null)

/** Pengumuman berupa modal tengah yang tidak mengunci apa pun: ditutup lewat tombol, ketuk di luar, atau tombol kembali. */
@Composable
fun NoticeSheet(
    title: String,
    items: List<NoticeSheetItem>,
    closeLabel: String,
    onClose: () -> Unit,
) {
    AppDialog(title = title, onDismiss = onClose) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(AppTheme.spacing.lg),
            verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
        ) {
            Column {
                items.forEachIndexed { index, item ->
                    if (index > 0) AppDivider()
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(vertical = AppTheme.spacing.md),
                        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
                    ) {
                        item.icon?.let { NoticeIcon(it) }
                        Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs)) {
                            AppText(text = item.title, role = TextRole.Caption, color = AppTheme.colors.content)
                            item.caption?.let { AppText(text = it, role = TextRole.Caption, color = AppTheme.colors.contentMuted) }
                        }
                    }
                }
            }
            PrimaryButton(text = closeLabel, onClick = onClose)
        }
    }
}

/** Ubin ikon butir pengumuman: ikon warna teks di atas latar warna aksen. */
@Composable
private fun NoticeIcon(icon: ImageVector) {
    val colors = AppTheme.colors
    Box(
        modifier = Modifier
            .size(AppTheme.sizes.control)
            .clip(AppTheme.shapes.field)
            .background(colors.accent),
        contentAlignment = Alignment.Center,
    ) {
        AppIcon(icon = icon, tint = colors.content, size = AppTheme.sizes.iconSmall)
    }
}
