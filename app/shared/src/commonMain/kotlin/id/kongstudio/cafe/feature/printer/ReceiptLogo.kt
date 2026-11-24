package id.kongstudio.cafe.feature.printer

import id.kongstudio.cafe.resources.Res
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

private const val Esc = 0x1B
private const val Fs = 0x1C
private const val LineFeed = 0x0A
private const val AlignCenter = 1
private const val StoredImageNumber = 1
private const val NormalScale = 0

/** Logo kepala struk sama dengan kasir web (lebar 200 titik, ambang 160), dikirim sebagai raster lengkap [full] atau panggilan logo tersimpan [stored] setelah kasir memastikan printernya mendukung. */
object ReceiptLogo {
    /** Naikkan bila gambar logo berganti, supaya printer yang menyimpan logo lama memakai raster lengkap lagi. */
    const val Version = 1

    private const val FullPath = "files/receipt/logo-struk-200.bin"
    private const val DefinePath = "files/receipt/logo-struk-200-nv.bin"

    private val lock = Mutex()
    private var fullBytes: ByteArray? = null

    /** Rata tengah, gambar raster per pita 24 baris, lalu baris baru; byte persis seperti yang dikirim web. */
    suspend fun full(): ByteArray? = lock.withLock {
        fullBytes ?: runCatching { Res.readBytes(FullPath) }.getOrNull()?.also { fullBytes = it }
    }

    /** Rata tengah, cetak gambar tersimpan nomor 1 (FS p), lalu baris baru. */
    val stored: ByteArray = byteArrayOf(
        Esc.toByte(), 'a'.code.toByte(), AlignCenter.toByte(),
        Fs.toByte(), 'p'.code.toByte(), StoredImageNumber.toByte(), NormalScale.toByte(),
        LineFeed.toByte(),
    )

    /** Perintah FS q yang menyimpan logo ke memori printer; dikirim sekali dari layar printer, bukan setiap struk. */
    suspend fun define(): ByteArray? = runCatching { Res.readBytes(DefinePath) }.getOrNull()

    /** Logo untuk satu struk pada [printer]: tidak ada bila dimatikan, yang tersimpan bila versinya cocok, selain itu raster lengkap. */
    suspend fun forPrinter(printer: PairedPrinter): ByteArray? = when {
        printer.logoOff -> null
        printer.logoVersion == Version -> stored
        else -> full()
    }
}
