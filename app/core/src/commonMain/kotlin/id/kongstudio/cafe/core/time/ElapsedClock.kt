package id.kongstudio.cafe.core.time

import kotlin.time.TimeSource

/** Jam perangkat yang terus berjalan saat perangkat tidur dan kembali ke nol setelah dihidupkan ulang, tidak terpengaruh jam dinding yang bisa diubah pengguna. */
interface ElapsedClock {
    fun elapsedMillis(): Long

    /** Penanda satu kali hidup perangkat, berubah setiap dihidupkan ulang; null bila tidak bisa dibaca, dan jangkar waktu tidak disimpan. */
    val bootId: String?
}

/** Cadangan untuk platform tanpa jam yang tahan tidur: hanya berlaku selama proses ini hidup, dan tidak punya penanda hidup perangkat. */
internal object ProcessElapsedClock : ElapsedClock {
    private val start = TimeSource.Monotonic.markNow()

    override fun elapsedMillis(): Long = start.elapsedNow().inWholeMilliseconds

    override val bootId: String? = null
}

/** Jangkar waktu server yang bisa disimpan: [serverEpochMillis] adalah waktu server saat dibaca, dan [elapsedAtMillis] pembacaan [ElapsedClock] saat itu pada hidup perangkat [bootId]. */
data class AnchorSnapshot(val serverEpochMillis: Long, val elapsedAtMillis: Long, val bootId: String)
