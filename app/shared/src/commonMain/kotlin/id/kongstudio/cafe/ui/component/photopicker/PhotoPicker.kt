package id.kongstudio.cafe.ui.component.photopicker

import androidx.compose.runtime.Composable

/** Foto hasil pilihan yang sudah dikonversi menjadi JPEG berukuran wajar, siap diunggah. */
class PickedPhoto(val bytes: ByteArray)

interface PhotoPicker {
    /** Membuka pemilih galeri; hasilnya diterima lewat `onPicked` pada [rememberPhotoPicker]. */
    fun pickFromGallery()

    /** Membuka kamera untuk mengambil satu foto; hasilnya diterima lewat `onPicked`. */
    fun takePhoto()
}

/** Pemilih foto dari galeri atau kamera: gambar apa pun diterima, lalu dikonversi dan diperkecil otomatis sehingga pengguna tidak pernah menemui batas ukuran atau format. */
@Composable
expect fun rememberPhotoPicker(onPicked: (PickedPhoto) -> Unit): PhotoPicker
