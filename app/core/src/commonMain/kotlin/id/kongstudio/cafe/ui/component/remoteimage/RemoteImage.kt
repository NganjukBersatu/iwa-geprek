package id.kongstudio.cafe.ui.component.remoteimage

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import coil3.compose.AsyncImage
import id.kongstudio.cafe.ui.theme.AppTheme

/** Foto kecil persegi seukuran [id.kongstudio.cafe.ui.component.iconbadge.IconBadge], untuk menggantikan ikon baris daftar bila foto ada. */
@Composable
fun RemoteThumbnail(url: String, contentDescription: String?, modifier: Modifier = Modifier) {
    NetworkImage(
        url = url,
        contentDescription = contentDescription,
        compact = true,
        modifier = modifier
            .size(AppTheme.spacing.compactTarget)
            .clip(AppTheme.shapes.pill)
            .background(AppTheme.colors.selected),
    )
}

/** Gambar jaringan yang dipotong mengisi bingkai [AppTheme.sizes.photoAspectRatio], atau tampil utuh selebar tempatnya bila [fit]. */
@Composable
fun RemoteImage(
    url: String,
    contentDescription: String?,
    modifier: Modifier = Modifier,
    fit: Boolean = false,
) {
    if (fit) {
        AsyncImage(
            model = url,
            contentDescription = contentDescription,
            contentScale = ContentScale.FillWidth,
            modifier = modifier.fillMaxWidth().clip(AppTheme.shapes.field).background(AppTheme.colors.selected),
        )
        return
    }
    Box(
        modifier = modifier
            .fillMaxWidth()
            .aspectRatio(AppTheme.sizes.photoAspectRatio)
            .clip(AppTheme.shapes.field)
            .background(AppTheme.colors.selected),
    ) {
        NetworkImage(url = url, contentDescription = contentDescription, modifier = Modifier.matchParentSize())
    }
}

/** Gambar jaringan yang dipotong memenuhi bingkai induknya; ukuran bingkai ditentukan pemanggil. */
@Composable
fun RemoteImageFill(
    url: String,
    contentDescription: String?,
    modifier: Modifier = Modifier,
) {
    AsyncImage(
        model = url,
        contentDescription = contentDescription,
        contentScale = ContentScale.Crop,
        modifier = modifier.fillMaxSize().background(AppTheme.colors.selected),
    )
}
