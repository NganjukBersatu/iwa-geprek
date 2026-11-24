package id.kongstudio.cafe.core.time

import kotlin.concurrent.Volatile
import kotlin.time.Clock
import kotlin.time.ExperimentalTime

/** Satu-satunya sumber "sekarang" di app: jam server dari header `Date` dihitung maju dengan [ElapsedClock] yang ikut berjalan saat tidur, memakai jam perangkat sampai jangkar pertama. */
object ServerClock {
    private class Anchor(val epochMillis: Long, val elapsedAtMillis: Long, val bootId: String?)

    /** Jangkar yang sama tidak dilaporkan lebih sering dari ini, supaya penyimpanannya tidak ditulis di setiap respons. */
    private const val REPORT_EVERY_MILLIS = 60_000L

    @Volatile
    private var anchor: Anchor? = null

    @Volatile
    private var clock: ElapsedClock = ProcessElapsedClock

    @Volatile
    private var reportedAtMillis: Long? = null

    /** Dipanggil dengan jangkar yang layak disimpan, di thread yang membaca respons, jadi isinya tidak boleh menunggu. */
    @Volatile
    var onAnchored: ((AnchorSnapshot) -> Unit)? = null

    /** Dipanggil sekali saat aplikasi mulai, sebelum respons pertama dibaca. */
    fun install(elapsedClock: ElapsedClock) {
        clock = elapsedClock
    }

    /** True bila jam server sudah terbaca di proses ini, sehingga [nowEpochMillis] bukan jam perangkat. */
    val isAnchored: Boolean get() = anchor != null

    @OptIn(ExperimentalTime::class)
    fun nowEpochMillis(): Long {
        val current = anchor ?: return Clock.System.now().toEpochMilliseconds()
        return current.epochMillis + (clock.elapsedMillis() - current.elapsedAtMillis)
    }

    fun nowEpochSeconds(): Long = nowEpochMillis() / 1000

    /** [httpDate] berformat RFC 1123, contoh "Wed, 14 Oct 2026 08:00:00 GMT"; yang tidak terbaca diabaikan. */
    fun sync(httpDate: String?) {
        val millis = parseHttpDate(httpDate) ?: return
        val fresh = Anchor(millis, clock.elapsedMillis(), clock.bootId)
        anchor = fresh
        report(fresh)
    }

    /** Memulihkan jangkar yang disimpan; ditolak bila perangkat sudah dihidupkan ulang sejak itu, atau bila sudah ada jangkar yang lebih baru. */
    fun restore(snapshot: AnchorSnapshot): Boolean {
        if (anchor != null) return false
        if (snapshot.bootId != clock.bootId || clock.elapsedMillis() < snapshot.elapsedAtMillis) return false
        anchor = Anchor(snapshot.serverEpochMillis, snapshot.elapsedAtMillis, snapshot.bootId)
        return true
    }

    private fun report(fresh: Anchor) {
        val boot = fresh.bootId ?: return
        val listener = onAnchored ?: return
        val last = reportedAtMillis
        if (last != null && fresh.elapsedAtMillis - last < REPORT_EVERY_MILLIS) return
        reportedAtMillis = fresh.elapsedAtMillis
        listener(AnchorSnapshot(fresh.epochMillis, fresh.elapsedAtMillis, boot))
    }

    private val MonthNames = listOf("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

    private fun parseHttpDate(value: String?): Long? {
        val parts = value?.replace(",", "")?.trim()?.split(' ')?.filter { it.isNotEmpty() } ?: return null
        // [hari, tanggal, bulan, tahun, jam, zona]
        if (parts.size < 5) return null
        val offset = if (parts[0].length == 3 && parts[0][0].isLetter()) 1 else 0
        val day = parts.getOrNull(offset)?.toIntOrNull() ?: return null
        val month = MonthNames.indexOf(parts.getOrNull(offset + 1)?.take(3)).takeIf { it >= 0 }?.plus(1) ?: return null
        val year = parts.getOrNull(offset + 2)?.toIntOrNull() ?: return null
        val clock = parts.getOrNull(offset + 3)?.split(':')?.mapNotNull { it.toIntOrNull() } ?: return null
        if (clock.size != 3) return null

        val shiftedYear = if (month <= 2) year - 1 else year
        val era = shiftedYear.floorDiv(400)
        val yearOfEra = shiftedYear - era * 400
        val dayOfYear = (153 * (month + if (month > 2) -3 else 9) + 2) / 5 + day - 1
        val dayOfEra = yearOfEra * 365 + yearOfEra / 4 - yearOfEra / 100 + dayOfYear
        val days = era * 146_097L + dayOfEra - 719_468L
        return (days * 86_400L + clock[0] * 3_600L + clock[1] * 60L + clock[2]) * 1000L
    }
}
