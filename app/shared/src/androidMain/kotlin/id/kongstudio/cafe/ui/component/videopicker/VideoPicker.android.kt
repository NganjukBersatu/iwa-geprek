package id.kongstudio.cafe.ui.component.videopicker

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
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
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

private const val VIDEO_DIR = "photos"
private const val UNKNOWN_SIZE = -1L
private const val MP4 = ".mp4"
private const val MOV = ".mov"
private const val WEBM = ".webm"

@Composable
actual fun rememberVideoPicker(onPicked: (PickedVideo) -> Unit, onTooLarge: () -> Unit): VideoPicker {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val picked = rememberUpdatedState(onPicked)
    val tooLarge = rememberUpdatedState(onTooLarge)
    // Disimpan agar tetap ada bila proses ditutup sistem selagi kamera terbuka.
    var capturePath by rememberSaveable { mutableStateOf<String?>(null) }
    // Penanda kotak izin kamera sedang tampil, agar ketukan berulang tidak memunculkan kotak kedua.
    var askingCamera by rememberSaveable { mutableStateOf(false) }

    val camera = rememberLauncherForActivityResult(ActivityResultContracts.CaptureVideo()) { saved ->
        val file = capturePath?.let(::File)
        capturePath = null
        scope.launch {
            if (saved && file != null) deliverVideo(file.length(), MP4, picked.value, tooLarge.value) { file.readBytes() }
            file?.let { withContext(Dispatchers.IO) { it.delete() } }
        }
    }

    /** Perangkat tanpa aplikasi kamera (sebagian tablet) menolak dibuka; itu berarti tidak ada video, bukan aplikasi tertutup. */
    fun openCamera() {
        val opened = runCatching {
            val file = newCaptureFile(context)
            capturePath = file.absolutePath
            camera.launch(FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file))
        }
        if (opened.isFailure) capturePath?.let { File(it).delete() }.also { capturePath = null }
    }

    // Manifest mendeklarasikan CAMERA, jadi kamera bawaan menolak dengan SecurityException selama izinnya belum diberikan.
    val cameraPermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        askingCamera = false
        if (granted) openCamera()
    }

    return remember(camera, cameraPermission) {
        object : VideoPicker {
            override fun record() {
                if (capturePath != null || askingCamera) return
                if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                    openCamera()
                } else {
                    askingCamera = runCatching { cameraPermission.launch(Manifest.permission.CAMERA) }.isSuccess
                }
            }
        }
    }
}

/** Membaca video dari [uri] galeri; yang melewati [MaxVideoBytes] tidak dibaca dan dilaporkan lewat [onTooLarge]. */
internal suspend fun readVideo(context: Context, uri: Uri, onPicked: (PickedVideo) -> Unit, onTooLarge: () -> Unit) {
    val size = withContext(Dispatchers.IO) { sizeOf(context, uri) }
    val extension = extensionOf(context.contentResolver.getType(uri))
    deliverVideo(size, extension, onPicked, onTooLarge) { context.contentResolver.openInputStream(uri)?.use { it.readBytes() } }
}

private suspend fun deliverVideo(
    size: Long,
    extension: String,
    onPicked: (PickedVideo) -> Unit,
    onTooLarge: () -> Unit,
    read: () -> ByteArray?,
) {
    if (size > MaxVideoBytes) {
        onTooLarge()
        return
    }
    val bytes = withContext(Dispatchers.IO) { runCatching(read).getOrNull() } ?: return
    if (bytes.size > MaxVideoBytes) onTooLarge() else onPicked(PickedVideo(bytes, extension))
}

private fun newCaptureFile(context: Context): File {
    val dir = File(context.cacheDir, VIDEO_DIR).apply { mkdirs() }
    return File.createTempFile("capture_", MP4, dir)
}

private fun sizeOf(context: Context, uri: Uri): Long =
    runCatching { context.contentResolver.openAssetFileDescriptor(uri, "r")?.use { it.length } }
        .getOrNull() ?: UNKNOWN_SIZE

private fun extensionOf(mimeType: String?): String = when (mimeType) {
    "video/quicktime" -> MOV
    "video/webm" -> WEBM
    else -> MP4
}
