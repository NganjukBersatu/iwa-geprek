package id.kongstudio.cafe.ui.component.photopicker

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
import id.kongstudio.cafe.core.image.PhotoConverter
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

private const val PHOTO_DIR = "photos"

@Composable
actual fun rememberPhotoPicker(onPicked: (PickedPhoto) -> Unit): PhotoPicker {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val callback = rememberUpdatedState(onPicked)
    // Disimpan agar tetap ada bila proses ditutup sistem selagi kamera terbuka.
    var capturePath by rememberSaveable { mutableStateOf<String?>(null) }
    // Penanda galeri sedang terbuka, agar ketukan berulang tidak membuka pemilih kedua.
    var galleryOpen by rememberSaveable { mutableStateOf(false) }
    // Penanda kotak izin kamera sedang tampil, dengan alasan yang sama.
    var askingCamera by rememberSaveable { mutableStateOf(false) }

    suspend fun deliver(raw: ByteArray?) {
        val jpeg = raw?.let { PhotoConverter.toUploadJpeg(it) } ?: return
        callback.value(PickedPhoto(jpeg))
    }

    val gallery = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        galleryOpen = false
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch { readPhoto(context, uri)?.let(callback.value) }
    }

    val camera = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { saved ->
        val file = capturePath?.let(::File)
        capturePath = null
        scope.launch {
            val raw = if (saved && file != null) {
                withContext(Dispatchers.IO) { runCatching { file.readBytes() }.getOrNull() }
            } else {
                null
            }
            file?.let { withContext(Dispatchers.IO) { it.delete() } }
            deliver(raw)
        }
    }

    /** Perangkat tanpa aplikasi kamera (sebagian tablet) menolak dibuka; itu berarti tidak ada foto, bukan aplikasi tertutup. */
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

    return remember(gallery, camera, cameraPermission) {
        object : PhotoPicker {
            override fun pickFromGallery() {
                if (galleryOpen || capturePath != null || askingCamera) return
                galleryOpen = runCatching { gallery.launch("image/*") }.isSuccess
            }

            override fun takePhoto() {
                if (galleryOpen || capturePath != null || askingCamera) return
                if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                    openCamera()
                } else {
                    askingCamera = runCatching { cameraPermission.launch(Manifest.permission.CAMERA) }.isSuccess
                }
            }
        }
    }
}

/** Membaca foto dari [uri] galeri lalu mengonversinya menjadi JPEG siap unggah; null bila tidak terbaca. */
internal suspend fun readPhoto(context: Context, uri: Uri): PickedPhoto? {
    val raw = withContext(Dispatchers.IO) {
        runCatching { context.contentResolver.openInputStream(uri)?.use { it.readBytes() } }.getOrNull()
    }
    return raw?.let { PhotoConverter.toUploadJpeg(it) }?.let(::PickedPhoto)
}

private fun newCaptureFile(context: Context): File {
    val dir = File(context.cacheDir, PHOTO_DIR).apply { mkdirs() }
    return File.createTempFile("capture_", ".jpg", dir)
}
