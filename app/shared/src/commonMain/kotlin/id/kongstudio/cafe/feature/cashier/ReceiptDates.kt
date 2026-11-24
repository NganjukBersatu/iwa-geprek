package id.kongstudio.cafe.feature.cashier

import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.months
import id.kongstudio.cafe.resources.months_short
import id.kongstudio.cafe.resources.weekdays_long
import org.jetbrains.compose.resources.getStringArray

// Nama hari dan bulan dibaca dari strings.xml (array weekdays_long, months, months_short), satu sumber dengan layar.

/** "Sabtu, 25 Oktober 2026, 14.05" (WIB), seperti baris Waktu dan Terbayar di struk web. */
internal suspend fun receiptDateTime(epochSeconds: Long): String {
    val stamp = DateTimeFormat.stampAt(epochSeconds)
    val day = getStringArray(Res.array.weekdays_long)[DateTimeFormat.weekdayIndex(stamp.date)]
    val month = getStringArray(Res.array.months)[DateTimeFormat.monthIndex(stamp.date)]
    return "$day, ${stamp.date.substring(8, 10)} $month ${stamp.date.take(4)}, ${stamp.time.replace(':', '.')}"
}

/** "25 Okt 26, 14.05" (WIB), seperti baris Waktu di tiket bar/dapur web. */
internal suspend fun ticketDateTime(epochSeconds: Long): String {
    val stamp = DateTimeFormat.stampAt(epochSeconds)
    val month = getStringArray(Res.array.months_short)[DateTimeFormat.monthIndex(stamp.date)]
    return "${stamp.date.substring(8, 10)} $month ${stamp.date.substring(2, 4)}, ${stamp.time.replace(':', '.')}"
}
