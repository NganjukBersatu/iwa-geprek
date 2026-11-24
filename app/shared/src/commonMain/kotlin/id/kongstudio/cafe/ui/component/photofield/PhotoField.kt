package id.kongstudio.cafe.ui.component.photofield

import androidx.compose.foundation.Image
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.photo_camera
import id.kongstudio.cafe.resources.photo_gallery
import id.kongstudio.cafe.ui.component.photopicker.PickedPhoto
import id.kongstudio.cafe.ui.component.photopicker.rememberPhotoPicker
import id.kongstudio.cafe.ui.component.sourcebutton.SourceButton
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import org.jetbrains.compose.resources.decodeToImageBitmap
import org.jetbrains.compose.resources.stringResource

/** Kolom foto: pratinjau pilihan, tombol kamera dan galeri (galeri bisa dimatikan lewat [allowGallery]), dengan hasil dikonversi otomatis dan diterima lewat [onPicked]. */
@Composable
fun PhotoField(
    photo: PickedPhoto?,
    onPicked: (PickedPhoto) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    allowGallery: Boolean = true,
) {
    val colors = AppTheme.colors
    val picker = rememberPhotoPicker(onPicked)

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
    ) {
        if (photo != null) {
            val bitmap = remember(photo) { photo.bytes.decodeToImageBitmap() }
            Image(
                bitmap = bitmap,
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(AppTheme.sizes.photoAspectRatio)
                    .clip(AppTheme.shapes.field)
                    .border(AppTheme.sizes.borderThin, colors.divider, AppTheme.shapes.field),
            )
        }
        Row(horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm)) {
            SourceButton(
                label = stringResource(Res.string.photo_camera),
                icon = AppIcons.Camera,
                onClick = picker::takePhoto,
                enabled = enabled,
                modifier = Modifier.weight(1f),
            )
            if (allowGallery) {
                SourceButton(
                    label = stringResource(Res.string.photo_gallery),
                    icon = AppIcons.Photo,
                    onClick = picker::pickFromGallery,
                    enabled = enabled,
                    modifier = Modifier.weight(1f),
                )
            }
        }
    }
}
