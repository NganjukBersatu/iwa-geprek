package id.kongstudio.cafe.core.format

import id.kongstudio.cafe.core.time.ServerClock

/** Format tanggal dan jam kehadiran tanpa pustaka tanggal; seluruh jam ditampilkan dalam WIB (UTC+7). */
object DateTimeFormat {
    private const val WIB_OFFSET_MINUTES = 7 * 60
    private const val WIB_ZONE = "+07:00"
    private const val SECONDS_PER_DAY = 86_400L

    fun firstDay(month: YearMonth) = dateOf(month, 1)

    /** Bulan dalam bentuk YYYY-MM, seperti yang diminta rute rekap. */
    fun monthKey(month: YearMonth) = "${month.year}-${two(month.month)}"

    /** Tanggal "YYYY-MM-DD" untuk [day] pada [month]. */
    fun dateOf(month: YearMonth, day: Int) = "${month.year}-${two(month.month)}-${two(day)}"

    fun lastDay(month: YearMonth) = "${month.year}-${two(month.month)}-${two(daysInMonth(month))}"

    fun daysInMonth(month: YearMonth): Int = when (month.month) {
        2 -> if (isLeap(month.year)) 29 else 28
        4, 6, 9, 11 -> 30
        else -> 31
    }

    /** Indeks hari (0 = Minggu) dari tanggal "YYYY-MM-DD" (algoritma Sakamoto); tanggal yang tidak terbaca dianggap Minggu. */
    fun weekdayIndex(date: String): Int {
        val parts = date.take(10).split('-').mapNotNull { it.toIntOrNull() }
        if (parts.size < 3 || parts[1] !in 1..12) return 0
        val (y, m, d) = parts
        val offsets = intArrayOf(0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4)
        val year = if (m < 3) y - 1 else y
        val index = (year + year / 4 - year / 100 + year / 400 + offsets[m - 1] + d) % 7
        return index
    }

    fun dayOfMonth(date: String): String = date.drop(8).take(2).trimStart('0')

    fun monthIndex(date: String): Int = ((date.drop(5).take(2).toIntOrNull() ?: 1) - 1).coerceIn(0, 11)

    /** Tanggal hari ini menurut WIB, "YYYY-MM-DD", dari jam server. */
    fun todayWib(): String = stampAt(ServerClock.nowEpochSeconds()).date

    /** Jam WIB (0 sampai 23) dari detik sejak epoch. */
    fun hourAt(epochSeconds: Long): Int = ((epochSeconds + WIB_OFFSET_MINUTES * 60L).mod(SECONDS_PER_DAY) / 3_600L).toInt()

    /** Tanggal WIB [days] hari sebelum hari ini, "YYYY-MM-DD". */
    fun daysAgo(days: Int): String = stampAt(ServerClock.nowEpochSeconds() - days * SECONDS_PER_DAY).date

    /** Tanggal dan jam WIB dari detik sejak epoch. */
    fun stampAt(epochSeconds: Long): WibStamp {
        val seconds = epochSeconds + WIB_OFFSET_MINUTES * 60L
        val z = seconds.floorDiv(86_400L) + 719_468L
        val era = z.floorDiv(146_097L)
        val dayOfEra = z - era * 146_097L
        val yearOfEra = (dayOfEra - dayOfEra / 1_460 + dayOfEra / 36_524 - dayOfEra / 146_096) / 365
        val dayOfYear = dayOfEra - (365 * yearOfEra + yearOfEra / 4 - yearOfEra / 100)
        val monthPart = (5 * dayOfYear + 2) / 153
        val day = dayOfYear - (153 * monthPart + 2) / 5 + 1
        val month = if (monthPart < 10) monthPart + 3 else monthPart - 9
        val year = yearOfEra + era * 400 + if (month <= 2) 1 else 0
        val minuteOfDay = (seconds.mod(86_400L) / 60).toInt()
        return WibStamp(
            date = "$year-${two(month.toInt())}-${two(day.toInt())}",
            time = clockOf(minuteOfDay),
        )
    }

    /** Jam "HH:MM" dari menit sejak tengah malam. */
    fun clockOf(minuteOfDay: Int) = "${two(minuteOfDay / 60)}:${two(minuteOfDay % 60)}"

    /** Stempel ISO 8601 berzona WIB dari tanggal "YYYY-MM-DD" dan jam "HH:MM", untuk dikirim ke server. */
    fun wibIso(date: String, time: String) = "${date}T$time:00$WIB_ZONE"

    /** Bulan dari tanggal "YYYY-MM-DD". */
    fun monthOf(date: String) = YearMonth(date.substring(0, 4).toInt(), date.substring(5, 7).toInt())

    /** Tanggal dan jam WIB dari stempel ISO (tanpa zona dianggap UTC), dan stempel yang tak terbaca menjadi null karena ini dipanggil saat layar digambar. */
    fun stamp(iso: String?): WibStamp? {
        if (iso == null || iso.length < 16) return null
        val time = iso.substringAfter('T', "")
        if (time.length < 5) return null
        val hour = time.substring(0, 2).toIntOrNull() ?: return null
        val minute = time.substring(3, 5).toIntOrNull() ?: return null
        val zoneStart = time.indexOfFirst { it == 'Z' || it == '+' || it == '-' }
        val offset = if (zoneStart < 0 || time[zoneStart] == 'Z') {
            0
        } else {
            val sign = if (time[zoneStart] == '-') -1 else 1
            val zone = time.substring(zoneStart + 1)
            val zoneHours = zone.take(2).toIntOrNull() ?: return null
            val zoneMinutes = zone.drop(3).take(2).ifEmpty { "0" }.toIntOrNull() ?: return null
            sign * (zoneHours * 60 + zoneMinutes)
        }
        val shifted = hour * 60 + minute - offset + WIB_OFFSET_MINUTES
        val dayDelta = shifted.floorDiv(1440)
        val wib = shifted - dayDelta * 1440
        return WibStamp(
            date = shiftDate(iso.substringBefore('T'), dayDelta) ?: return null,
            time = clockOf(wib),
        )
    }

    fun clock(iso: String?): String? = stamp(iso)?.time

    private fun shiftDate(date: String, delta: Int): String? {
        if (delta == 0) return date
        val parts = date.split('-').mapNotNull { it.toIntOrNull() }
        if (parts.size < 3) return null
        var month = YearMonth(parts[0], parts[1])
        var day = parts[2] + delta
        if (day > daysInMonth(month)) {
            month = month.next()
            day = 1
        } else if (day < 1) {
            month = month.previous()
            day = daysInMonth(month)
        }
        return "${month.year}-${two(month.month)}-${two(day)}"
    }

    /** Selisih menit dua jam "HH:MM"; selesai yang tidak lebih besar dari mulai berarti lewat tengah malam. */
    fun spanMinutes(start: String, end: String): Int {
        val from = start.substring(0, 2).toInt() * 60 + start.substring(3, 5).toInt()
        val to = end.substring(0, 2).toInt() * 60 + end.substring(3, 5).toInt()
        return if (to > from) to - from else to + 1440 - from
    }

    /** Jam dan menit (menit dua digit) untuk diisikan ke format durasi. */
    fun durationParts(totalMinutes: Int): Pair<String, String> =
        (totalMinutes / 60).toString() to two(totalMinutes % 60)

    private fun isLeap(year: Int) = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)

    private fun two(value: Int) = value.toString().padStart(2, '0')
}

class WibStamp(val date: String, val time: String) {
    /** Kunci urut kronologis; leksikografis cukup karena formatnya tetap. */
    val sortKey: String get() = "$date $time"
}

data class YearMonth(val year: Int, val month: Int) {
    fun previous() = if (month == 1) YearMonth(year - 1, 12) else YearMonth(year, month - 1)

    fun next() = if (month == 12) YearMonth(year + 1, 1) else YearMonth(year, month + 1)
}
