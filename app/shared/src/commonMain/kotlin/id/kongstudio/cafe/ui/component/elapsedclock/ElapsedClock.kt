package id.kongstudio.cafe.ui.component.elapsedclock

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import id.kongstudio.cafe.core.time.ServerClock
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import kotlinx.coroutines.delay

private const val SpinMillis = 6_000
private const val TickMillis = 1_000L
private const val FullTurn = 360f
private const val SecondsPerMinute = 60L
private const val SecondsPerHour = 3_600L

/** Ikon jam yang terus berputar dengan lama berjalan sejak [sinceEpoch] di bawahnya; hanya penanda waktu. */
@Composable
fun ElapsedClock(sinceEpoch: Long, modifier: Modifier = Modifier) {
    val colors = AppTheme.colors
    var now by remember { mutableLongStateOf(ServerClock.nowEpochSeconds()) }
    LaunchedEffect(Unit) {
        while (true) {
            delay(TickMillis)
            now = ServerClock.nowEpochSeconds()
        }
    }
    val angle by rememberInfiniteTransition(label = "elapsed-clock").animateFloat(
        initialValue = 0f,
        targetValue = FullTurn,
        animationSpec = infiniteRepeatable(tween(SpinMillis, easing = LinearEasing), RepeatMode.Restart),
        label = "elapsed-clock-angle",
    )

    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs),
    ) {
        AppIcon(
            icon = AppIcons.Clock,
            tint = colors.contentMuted,
            size = AppTheme.sizes.iconSmall,
            modifier = Modifier.graphicsLayer { rotationZ = angle },
        )
        BasicText(
            text = formatElapsed((now - sinceEpoch).coerceAtLeast(0L)),
            style = AppTheme.typography.caption.copy(color = colors.contentMuted),
        )
    }
}

private fun formatElapsed(seconds: Long): String {
    val hours = seconds / SecondsPerHour
    val minutes = seconds % SecondsPerHour / SecondsPerMinute
    val rest = seconds % SecondsPerMinute
    fun two(value: Long) = value.toString().padStart(2, '0')
    return if (hours > 0) "$hours:${two(minutes)}:${two(rest)}" else "${two(minutes)}:${two(rest)}"
}
