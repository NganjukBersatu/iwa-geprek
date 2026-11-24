package id.kongstudio.cafe.ui.component.photopair

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.ui.component.imagepreview.ImagePreviewDialog
import id.kongstudio.cafe.ui.component.photocard.PhotoCard
import id.kongstudio.cafe.ui.theme.AppTheme

class PhotoItem(val url: String?, val caption: String)

/** Dua foto bersebelahan dengan keterangan dan pratinjau layar penuh saat diketuk, dengan yang kosong menyisakan ruangnya dan keduanya kosong tidak tampil. */
@Composable
fun PhotoPair(
    first: PhotoItem,
    second: PhotoItem,
    modifier: Modifier = Modifier,
) {
    if (first.url == null && second.url == null) return
    var previewUrl by remember { mutableStateOf<String?>(null) }

    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.md),
    ) {
        listOf(first, second).forEach { item ->
            val url = item.url
            if (url != null) {
                PhotoCard(
                    url = url,
                    caption = item.caption,
                    onClick = { previewUrl = url },
                    modifier = Modifier.weight(1f),
                )
            } else {
                Spacer(Modifier.weight(1f))
            }
        }
    }

    previewUrl?.let { url -> ImagePreviewDialog(url = url, onDismiss = { previewUrl = null }) }
}
