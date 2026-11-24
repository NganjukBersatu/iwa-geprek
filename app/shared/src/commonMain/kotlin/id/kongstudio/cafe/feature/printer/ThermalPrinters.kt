package id.kongstudio.cafe.feature.printer

import kotlinx.coroutines.flow.StateFlow

/**
 * Slot printer di tablet: struk pembayaran, atau printer satu stasiun pembuat yang dikenali dari UUID stasiunnya.
 * [key] juga kunci penyimpanan pemasangan di tablet; kunci peran lama APK sebelumnya hanya dibaca untuk dipindahkan.
 */
class PrinterSlot private constructor(val key: String) {
    /** UUID stasiun untuk slot printer stasiun; null untuk struk pembayaran dan kunci lama. */
    val stationId: String? get() = key.removePrefix(StationPrefix).takeIf { key.startsWith(StationPrefix) }

    override fun equals(other: Any?): Boolean = other is PrinterSlot && other.key == key

    override fun hashCode(): Int = key.hashCode()

    override fun toString(): String = key

    companion object {
        private const val StationPrefix = "station:"

        val Receipt = PrinterSlot("Receipt")

        /** Kunci peran lama (Bar, Dapur, satu Printer Stasiun) yang dipindah ke slot stasiun lewat rencana cetak. */
        val LegacyBar = PrinterSlot("Bar")
        val LegacyKitchen = PrinterSlot("Kitchen")
        val LegacyStation = PrinterSlot("Station")
        val Legacy: List<PrinterSlot> = listOf(LegacyBar, LegacyKitchen, LegacyStation)

        fun station(stationId: String): PrinterSlot = PrinterSlot(StationPrefix + stationId)

        /** Membaca kunci tersimpan; kunci yang tidak dikenal dilewati supaya data rusak tidak menutup aplikasi. */
        fun fromKey(key: String): PrinterSlot? = when {
            key == Receipt.key -> Receipt
            key.startsWith(StationPrefix) && key.length > StationPrefix.length -> PrinterSlot(key)
            Legacy.any { it.key == key } -> PrinterSlot(key)
            else -> null
        }
    }
}

/** Lebar kertas; menentukan jumlah karakter per baris. */
enum class PaperSize(val millimeters: Int, val columns: Int) {
    Mm57(57, 32),
    Mm58(58, 32),
    Mm80(80, 48),
}

/** Printer yang terpasang pada satu slot dan tersimpan di tablet, dengan [logoVersion] versi logo di memori printer yang sudah dipastikan kasir atau null bila belum, dan [logoOff] bila struk dicetak tanpa logo. */
class PairedPrinter(val name: String, val address: String, val paper: PaperSize, val logoVersion: Int? = null, val logoOff: Boolean = false)

class DiscoveredPrinter(val name: String, val address: String)

enum class PrinterLink { NotPaired, Offline, Connecting, Ready }

sealed interface ScanOutcome {
    class Found(val printers: List<DiscoveredPrinter>) : ScanOutcome

    /** Izin Bluetooth ditolak pengguna. */
    data object NoPermission : ScanOutcome

    /** Bluetooth perangkat mati atau tidak tersedia. */
    data object BluetoothOff : ScanOutcome
}

sealed interface PrintOutcome {
    data object Ok : PrintOutcome

    data object NotPaired : PrintOutcome

    data object NoPermission : PrintOutcome

    data object BluetoothOff : PrintOutcome

    /** Printer mati atau di luar jangkauan. */
    data object Unreachable : PrintOutcome

    /** Perangkatnya tersambung tetapi tidak punya jalur untuk menerima data cetak, jadi bukan printer. */
    data object NotAPrinter : PrintOutcome

    /** Terputus di tengah pengiriman. */
    data object Interrupted : PrintOutcome
}

/** Printer termal Bluetooth yang pemasangannya disimpan per slot, dijaga tetap tersambung, dan disambung ulang sendiri bila putus. */
interface ThermalPrinters {
    val paired: StateFlow<Map<PrinterSlot, PairedPrinter>>
    val links: StateFlow<Map<PrinterSlot, PrinterLink>>

    /** Sambungan dijaga lewat layanan latar dengan notifikasi tetap, juga saat aplikasi ditutup; pilihan disimpan di tablet. */
    val keepAlive: StateFlow<Boolean>

    /** Menyalakan atau mematikan [keepAlive]; meminta izin notifikasi bila perlu, layanannya tetap jalan bila ditolak. */
    suspend fun setKeepAlive(enabled: Boolean)

    /** Mencari printer di sekitar beberapa detik; meminta izin Bluetooth bila belum ada. */
    suspend fun scan(): ScanOutcome

    /** Menyambung ke [device], lalu menyimpannya sebagai printer [slot]. */
    suspend fun pair(slot: PrinterSlot, device: DiscoveredPrinter): PrintOutcome

    suspend fun forget(slot: PrinterSlot)

    /** Memindah pemasangan dari [from] ke [to] bila [to] masih kosong; dipakai sekali untuk peran lama APK sebelumnya. */
    fun move(from: PrinterSlot, to: PrinterSlot)

    fun setPaper(slot: PrinterSlot, paper: PaperSize)

    /** Mencatat versi logo yang tersimpan di memori printer [slot]; null berarti logo dikirim lengkap setiap struk. */
    fun setLogoVersion(slot: PrinterSlot, version: Int?)

    /** Struk printer [slot] dicetak tanpa logo; data jauh lebih ringan untuk printer yang lambat. */
    fun setLogoOff(slot: PrinterSlot, off: Boolean)

    /** Menyambungkan ulang printer yang sudah dipasang tanpa mencetak, misalnya saat layar printer dibuka. */
    suspend fun reconnect(slot: PrinterSlot): PrintOutcome

    /** Mengirim byte ESC/POS ke printer [slot]; menyambung ulang sendiri bila terputus. */
    suspend fun print(slot: PrinterSlot, data: ByteArray): PrintOutcome
}
