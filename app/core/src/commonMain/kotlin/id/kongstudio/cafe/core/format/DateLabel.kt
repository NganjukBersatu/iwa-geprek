package id.kongstudio.cafe.core.format

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.format_date_plain
import id.kongstudio.cafe.resources.months
import org.jetbrains.compose.resources.stringArrayResource
import org.jetbrains.compose.resources.stringResource

/** Contoh: "12 Oktober 2026" dari "2026-10-12". */
@Composable
fun longDateLabel(date: String): String {
    val months = stringArrayResource(Res.array.months)
    return stringResource(
        Res.string.format_date_plain,
        DateTimeFormat.dayOfMonth(date),
        months[DateTimeFormat.monthIndex(date)],
        date.take(4),
    )
}
