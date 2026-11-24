package id.kongstudio.cafe.ui.component.pulsering

import androidx.compose.animation.core.LinearOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.drawOutline
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.scale
import id.kongstudio.cafe.ui.theme.AppTheme

/** Ukuran cincin saat muncul, sebagai bagian dari ukuran elemen; ia membesar sampai tepi sambil memudar. */
private const val RingStartScale = 0.78f
private const val RingStartAlpha = 0.85f

/** Cincin yang memudar keluar berulang dari tepi elemen sebagai penanda perhatian, dengan [active] false menghapus efek tanpa mengubah susunan. */
@Composable
fun Modifier.pulseRing(active: Boolean, color: Color, shape: Shape): Modifier {
    if (!active) return this
    val effects = AppTheme.effects
    val width = AppTheme.sizes.borderThick
    val progress by rememberInfiniteTransition(label = "pulse-ring").animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(effects.loopMillis, easing = LinearOutSlowInEasing),
            repeatMode = RepeatMode.Restart,
        ),
        label = "pulse-ring-progress",
    )

    return drawBehind {
        val outline = shape.createOutline(size, layoutDirection, this)
        scale(RingStartScale + (1f - RingStartScale) * progress) {
            drawOutline(
                outline = outline,
                color = color,
                alpha = RingStartAlpha * (1f - progress),
                style = Stroke(width = width.toPx()),
            )
        }
    }
}
