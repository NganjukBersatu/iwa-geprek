package id.kongstudio.cafe.ui.component.mediagallerypicker

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.ui.component.photopicker.PickedPhoto
import id.kongstudio.cafe.ui.component.videopicker.PickedVideo

interface MediaGalleryPicker {
    /** Membuka galeri yang menampilkan foto dan video sekaligus; hasilnya diterima lewat callback sesuai jenisnya. */
    fun pick()
}

/** Pemilih galeri tunggal untuk foto dan video: jenis berkas dikenali dari pilihannya, jadi pengguna tidak memilih jenis lebih dulu. */
@Composable
expect fun rememberMediaGalleryPicker(
    onPhoto: (PickedPhoto) -> Unit,
    onVideo: (PickedVideo) -> Unit,
    onTooLarge: () -> Unit,
): MediaGalleryPicker
