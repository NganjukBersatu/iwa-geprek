package id.kongstudio.cafe.ui.component.worktimer

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.ui.component.apptext.AppText
import id.kongstudio.cafe.ui.component.apptext.TextRole
import id.kongstudio.cafe.ui.component.badge.BadgeTone
import id.kongstudio.cafe.ui.component.badge.StatusBadge
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import id.kongstudio.cafe.ui.theme.AppTheme
import kotlinx.coroutines.delay

private const val TickMillis = 1_000L
private const val SecondsPerMinute = 60L
private const val SecondsPerHour = 3_600L

// Bagian jam kerja yang sedang dihitung; [Late] berarti target sudah lewat dan yang dihitung adalah keterlambatannya.
enum class TimerPhase { Counting, Remaining, Late }

// Hasil hitung satu saat; dipisah dari tampilan supaya daftar bisa mengurutkan dengan aturan yang sama.
data class TimerReading(val phase: TimerPhase, val seconds: Long)

// Tanpa target menghitung naik sejak [sinceEpoch]; dengan target menghitung mundur, lalu naik lagi sebagai keterlambatan.
fun readTimer(sinceEpoch: Long, targetSeconds: Int?, nowEpoch: Long): TimerReading {
    val passed = (nowEpoch - sinceEpoch).coerceAtLeast(0L)
    if (targetSeconds == null) return TimerReading(TimerPhase.Counting, passed)
    val left = targetSeconds - passed
    return if (left >= 0) TimerReading(TimerPhase.Remaining, left) else TimerReading(TimerPhase.Late, -left)
}

fun formatClock(seconds: Long): String {
    val hours = seconds / SecondsPerHour
    val minutes = seconds % SecondsPerHour / SecondsPerMinute
    val rest = seconds % SecondsPerMinute
    fun two(value: Long) = value.toString().padStart(2, '0')
    return if (hours > 0) "$hours:${two(minutes)}:${two(rest)}" else "${two(minutes)}:${two(rest)}"
}

// Jam kerja yang berdetak tiap detik dari jam server; [labels] memberi kata di bawah angka untuk tiap bagian.
@Composable
fun WorkTimer(
    sinceEpoch: Long,
    targetSeconds: Int?,
    labels: (TimerPhase) -> String,
    modifier: Modifier = Modifier,
    large: Boolean = false,
    horizontal: Alignment.Horizontal = Alignment.End,
) {
    val colors = AppTheme.colors
    var now by remember { mutableLongStateOf(ServerClock.nowEpochSeconds()) }
    LaunchedEffect(Unit) {
        while (true) {
            delay(TickMillis)
            now = ServerClock.nowEpochSeconds()
        }
    }
    val reading = readTimer(sinceEpoch, targetSeconds, now)
    val tint = when (reading.phase) {
        TimerPhase.Late -> colors.danger
        TimerPhase.Remaining -> colors.content
        TimerPhase.Counting -> colors.contentMuted
    }
    Column(modifier = modifier, horizontalAlignment = horizontal, verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs)) {
        AppText(text = formatClock(reading.seconds), role = if (large) TextRole.Title else TextRole.Subtitle, color = tint)
        AppText(text = labels(reading.phase), role = TextRole.Caption, color = if (reading.phase == TimerPhase.Late) colors.danger else colors.contentMuted)
    }
}

// Jam kerja dalam bentuk pil sebaris, untuk diletakkan berdampingan dengan lencana keadaan.
@Composable
fun WorkTimerPill(
    sinceEpoch: Long,
    targetSeconds: Int?,
    labels: (TimerPhase) -> String,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    var now by remember { mutableLongStateOf(ServerClock.nowEpochSeconds()) }
    LaunchedEffect(Unit) {
        while (true) {
            delay(TickMillis)
            now = ServerClock.nowEpochSeconds()
        }
    }
    val reading = readTimer(sinceEpoch, targetSeconds, now)
    val late = reading.phase == TimerPhase.Late
    StatusBadge(
        text = "${formatClock(reading.seconds)} ${labels(reading.phase)}",
        tone = if (late) BadgeTone.Danger else BadgeTone.Neutral,
        icon = AppIcons.Clock,
        modifier = modifier,
    )
}
