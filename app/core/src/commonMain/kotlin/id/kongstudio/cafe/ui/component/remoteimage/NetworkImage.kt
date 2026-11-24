package id.kongstudio.cafe.ui.component.remoteimage

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import coil3.compose.AsyncImage
import coil3.compose.AsyncImagePainter
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.remote_image_retry
import id.kongstudio.cafe.resources.remote_image_unavailable
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.stringResource

/** Gambar jaringan yang mengisi tempatnya; bila gagal dimuat tampil penanda "tidak tersedia" yang bisa diketuk untuk memuat ulang, atau hanya ikon kecil bila [compact] karena ketukannya milik baris induk. */
@Composable
fun NetworkImage(
    url: String,
    contentDescription: String?,
    modifier: Modifier = Modifier,
    contentScale: ContentScale = ContentScale.Crop,
    compact: Boolean = false,
) {
    var attempt by remember(url) { mutableIntStateOf(0) }
    var failed by remember(url) { mutableStateOf(false) }

    Box(modifier = modifier, contentAlignment = Alignment.Center) {
        // Kunci percobaan membuat permintaan baru saat memuat ulang, karena alamat yang sama tidak memicu muat ulang sendiri.
        key(attempt) {
            AsyncImage(
                model = url,
                contentDescription = contentDescription,
                contentScale = contentScale,
                onState = { state -> failed = state is AsyncImagePainter.State.Error },
                modifier = Modifier.matchParentSize(),
            )
        }
        if (failed) {
            Unavailable(compact = compact, onRetry = { attempt++ }, modifier = Modifier.matchParentSize())
        }
    }
}

@Composable
private fun Unavailable(compact: Boolean, onRetry: () -> Unit, modifier: Modifier) {
    val colors = AppTheme.colors
    if (compact) {
        Box(modifier = modifier, contentAlignment = Alignment.Center) {
            AppIcon(icon = AppIcons.PhotoOff, tint = colors.contentMuted, size = AppTheme.sizes.iconSmall)
        }
        return
    }
    Column(
        modifier = modifier
            .clickable(role = Role.Button, onClickLabel = stringResource(Res.string.remote_image_retry), onClick = onRetry)
            .padding(AppTheme.spacing.xs),
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs, Alignment.CenterVertically),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        AppIcon(icon = AppIcons.PhotoOff, tint = colors.contentMuted, size = AppTheme.sizes.iconLarge)
        AppText(
            text = stringResource(Res.string.remote_image_unavailable),
            role = TextRole.Caption,
            color = colors.contentMuted,
            textAlign = TextAlign.Center,
        )
    }
}
