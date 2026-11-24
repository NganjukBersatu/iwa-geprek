package id.kongstudio.cafe.ui.component.pdfpicker

import androidx.compose.runtime.Composable

/** Batas ukuran satu PDF yang diunggah; sama dengan batas lampiran izin di server. */
const val MaxPdfBytes = 5L * 1024 * 1024

/** PDF hasil pilihan yang sudah muat di [MaxPdfBytes]; [name] adalah nama berkas di perangkat untuk ditampilkan. */
class PickedPdf(val bytes: ByteArray, val name: String)

interface PdfPicker {
    /** Membuka pemilih dokumen sistem yang hanya menampilkan PDF; hasilnya diterima lewat `onPicked`. */
    fun pick()
}

/** Pemilih satu PDF dari perangkat; PDF di atas [MaxPdfBytes] diperkecil otomatis, sehingga pengguna tidak pernah ditolak karena ukuran. */
@Composable
expect fun rememberPdfPicker(onPicked: (PickedPdf) -> Unit): PdfPicker
