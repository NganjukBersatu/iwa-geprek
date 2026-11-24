package id.kongstudio.cafe.core.format

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.format_when
import id.kongstudio.cafe.resources.months_short
import id.kongstudio.cafe.resources.weekdays_short
import org.jetbrains.compose.resources.stringArrayResource
import org.jetbrains.compose.resources.stringResource

/** Contoh: "Sen 12 Okt · 08:00". */
@Composable
fun whenLabel(stamp: WibStamp): String {
    val weekdays = stringArrayResource(Res.array.weekdays_short)
    val months = stringArrayResource(Res.array.months_short)
    return stringResource(
        Res.string.format_when,
        weekdays[DateTimeFormat.weekdayIndex(stamp.date)],
        DateTimeFormat.dayOfMonth(stamp.date),
        months[DateTimeFormat.monthIndex(stamp.date)],
        stamp.time,
    )
}
