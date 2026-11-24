package id.kongstudio.cafe.feature.operational

import androidx.compose.runtime.Composable
import id.kongstudio.cafe.core.format.DateTimeFormat
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.greeting_afternoon
import id.kongstudio.cafe.resources.greeting_evening
import id.kongstudio.cafe.resources.greeting_morning
import id.kongstudio.cafe.resources.greeting_night
import org.jetbrains.compose.resources.stringResource

private const val MorningStartHour = 4
private const val AfternoonStartHour = 11
private const val EveningStartHour = 15
private const val NightStartHour = 18

/** Sapaan menurut jam WIB dari jam server; [name] kosong berarti sapaan saja. */
@Composable
internal fun greetingText(name: String?): String {
    val hour = DateTimeFormat.hourAt(ServerClock.nowEpochSeconds())
    val base = stringResource(
        when (hour) {
            in MorningStartHour until AfternoonStartHour -> Res.string.greeting_morning
            in AfternoonStartHour until EveningStartHour -> Res.string.greeting_afternoon
            in EveningStartHour until NightStartHour -> Res.string.greeting_evening
            else -> Res.string.greeting_night
        },
    )
    return if (name.isNullOrBlank()) base else "$base, $name"
}
