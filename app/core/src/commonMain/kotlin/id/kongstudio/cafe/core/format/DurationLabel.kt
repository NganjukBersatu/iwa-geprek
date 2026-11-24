package id.kongstudio.cafe.core.format

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.format_duration
import org.jetbrains.compose.resources.stringResource

/** Contoh: "2j 05m" dari 125 menit. */
@Composable
fun durationLabel(totalMinutes: Int): String {
    val (hours, minutes) = DateTimeFormat.durationParts(totalMinutes)
    return stringResource(Res.string.format_duration, hours, minutes)
}
