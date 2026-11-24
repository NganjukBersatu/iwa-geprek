package id.kongstudio.cafe.ui.component.photoreadbutton

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.photo_reading
import id.kongstudio.cafe.ui.component.button.PrimaryButton
import id.kongstudio.cafe.ui.component.photopicker.PickedPhoto
import id.kongstudio.cafe.ui.component.photopicker.rememberPhotoPicker
import org.jetbrains.compose.resources.stringResource

/** Tombol foto-lalu-baca: membuka kamera, [onPicked] menerima fotonya untuk dibaca server, dan [reading] menahan tombol selama dibaca. */
@Composable
fun PhotoReadButton(
    label: String,
    reading: Boolean,
    onPicked: (PickedPhoto) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
) {
    val picker = rememberPhotoPicker(onPicked)
    PrimaryButton(
        text = if (reading) stringResource(Res.string.photo_reading) else label,
        onClick = picker::takePhoto,
        modifier = modifier,
        enabled = enabled && !reading,
        loading = reading,
    )
}
