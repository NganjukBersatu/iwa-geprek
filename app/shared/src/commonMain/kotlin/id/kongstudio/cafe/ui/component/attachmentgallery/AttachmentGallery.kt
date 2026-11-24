package id.kongstudio.cafe.ui.component.attachmentgallery

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.imagepreview.ImagePreviewDialog
import id.kongstudio.cafe.ui.component.mediatile.MediaTile
import id.kongstudio.cafe.ui.component.remoteimage.NetworkImage
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

/** Satu lampiran tersimpan di server; [removable] false untuk lampiran lama yang tidak boleh dihapus. */
class RemoteAttachment(val id: String, val isVideo: Boolean, val url: String, val removable: Boolean)

/** Deretan lampiran: foto dibuka dengan pratinjau layar penuh, video dibuka di pemutar sistem, dan tombol hapus tampil bila [onRemove] diberikan. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun AttachmentGallery(
    attachments: List<RemoteAttachment>,
    modifier: Modifier = Modifier,
    onRemove: ((RemoteAttachment) -> Unit)? = null,
) {
    if (attachments.isEmpty()) return
    val uriHandler = LocalUriHandler.current
    var previewUrl by remember { mutableStateOf<String?>(null) }

    FlowRow(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
    ) {
        attachments.forEach { item ->
            Tile(
                item = item,
                onOpen = { if (item.isVideo) uriHandler.openUri(item.url) else previewUrl = item.url },
                onRemove = onRemove?.takeIf { item.removable }?.let { remove -> { remove(item) } },
            )
        }
    }

    previewUrl?.let { url -> ImagePreviewDialog(url = url, onDismiss = { previewUrl = null }) }
}

@Composable
private fun Tile(item: RemoteAttachment, onOpen: () -> Unit, onRemove: (() -> Unit)?) {
    MediaTile(onClick = onOpen, onRemove = onRemove) {
        if (item.isVideo) {
            AppIcon(icon = AppIcons.Video, tint = AppTheme.colors.primary, size = AppTheme.sizes.iconLarge)
        } else {
            NetworkImage(url = item.url, contentDescription = null, modifier = Modifier.matchParentSize())
        }
    }
}
