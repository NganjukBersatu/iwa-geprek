package id.kongstudio.cafe.core.image

/** Konversi foto untuk unggahan: format apa pun (JPEG, PNG, WebP, HEIC, ...) menjadi JPEG, orientasi dibetulkan, sisi terpanjang diperkecil. */
expect object PhotoConverter {
    /** JPEG siap unggah, atau null bila [raw] bukan gambar yang bisa dibaca. */
    suspend fun toUploadJpeg(raw: ByteArray): ByteArray?

    /** [jpeg] dengan kotak keterangan [stamp] di bagian bawah foto, tetap dalam batas ukuran unggah; null bila tidak terbaca. */
    suspend fun stamp(jpeg: ByteArray, stamp: PhotoStamp): ByteArray?
}

/** Satu baris cap foto; baris [bold] dicetak tebal dan lebih besar. */
class StampLine(val text: String, val bold: Boolean = false)

/** Isi dan warna cap foto; warna dalam ARGB. */
class PhotoStamp(val lines: List<StampLine>, val backgroundArgb: Int, val textArgb: Int)
