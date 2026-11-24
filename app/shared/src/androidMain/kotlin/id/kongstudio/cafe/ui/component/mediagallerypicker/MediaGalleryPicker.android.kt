package id.kongstudio.cafe.ui.component.mediagallerypicker

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import id.kongstudio.cafe.ui.component.photopicker.PickedPhoto
import id.kongstudio.cafe.ui.component.photopicker.readPhoto
import id.kongstudio.cafe.ui.component.videopicker.PickedVideo
import id.kongstudio.cafe.ui.component.videopicker.readVideo
import kotlinx.coroutines.launch

private const val VIDEO_TYPE_PREFIX = "video/"

@Composable
actual fun rememberMediaGalleryPicker(
    onPhoto: (PickedPhoto) -> Unit,
    onVideo: (PickedVideo) -> Unit,
    onTooLarge: () -> Unit,
): MediaGalleryPicker {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val photo = rememberUpdatedState(onPhoto)
    val video = rememberUpdatedState(onVideo)
    val tooLarge = rememberUpdatedState(onTooLarge)

    // Penanda pemilih sedang terbuka, agar ketukan berulang tidak membuka pemilih kedua.
    var open by rememberSaveable { mutableStateOf(false) }

    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        open = false
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch {
            if (context.contentResolver.getType(uri).orEmpty().startsWith(VIDEO_TYPE_PREFIX)) {
                readVideo(context, uri, video.value, tooLarge.value)
            } else {
                readPhoto(context, uri)?.let(photo.value)
            }
        }
    }

    return remember(launcher) {
        object : MediaGalleryPicker {
            override fun pick() {
                if (open) return
                // Tanpa aplikasi pemilih yang bisa dibuka, ketukan tidak berbuat apa-apa, bukan menutup aplikasi.
                open = runCatching { launcher.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageAndVideo)) }.isSuccess
            }
        }
    }
}
