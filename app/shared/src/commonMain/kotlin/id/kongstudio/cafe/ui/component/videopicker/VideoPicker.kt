package id.kongstudio.cafe.ui.component.videopicker

import androidx.compose.runtime.Composable

/** Batas ukuran satu video yang boleh diunggah; sama dengan batas di server. */
const val MaxVideoBytes = 30L * 1024 * 1024

/** Video hasil pilihan apa adanya; [extension] memuat titik, misalnya ".mp4". */
class PickedVideo(val bytes: ByteArray, val extension: String)

interface VideoPicker {
    /** Membuka kamera untuk merekam satu video; hasilnya diterima lewat `onPicked`. */
    fun record()
}

/** Perekam video kamera sistem yang tidak membaca video melewati [MaxVideoBytes] dan melaporkannya lewat [onTooLarge], sedangkan memilih dari galeri lewat `rememberMediaGalleryPicker`. */
@Composable
expect fun rememberVideoPicker(onPicked: (PickedVideo) -> Unit, onTooLarge: () -> Unit): VideoPicker
