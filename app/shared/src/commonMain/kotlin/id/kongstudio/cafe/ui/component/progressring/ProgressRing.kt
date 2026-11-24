package id.kongstudio.cafe.ui.component.progressring

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.Dp
import id.kongstudio.cafe.ui.theme.AppTheme

private const val StartAngle = -90f
private const val FullCircle = 360f
private const val FillDurationFactor = 2

/** Cincin kemajuan dengan label di tengah; terisi bertahap dari nol setiap kali nilainya berubah. */
@Composable
fun ProgressRing(
    progress: Float,
    label: String,
    trackColor: Color,
    indicatorColor: Color,
    labelColor: Color,
    modifier: Modifier = Modifier,
    size: Dp = AppTheme.sizes.avatarLarge,
) {
    val effects = AppTheme.effects
    val stroke = AppTheme.spacing.sm
    val filled = remember { Animatable(0f) }

    LaunchedEffect(progress) {
        filled.animateTo(
            targetValue = progress.coerceIn(0f, 1f),
            animationSpec = tween(effects.slowMillis * FillDurationFactor, easing = effects.emphasized),
        )
    }

    Box(modifier = modifier.size(size), contentAlignment = Alignment.Center) {
        Canvas(modifier = Modifier.size(size)) {
            val width = stroke.toPx()
            val arcSize = Size(this.size.width - width, this.size.height - width)
            val origin = Offset(width / 2f, width / 2f)
            val style = Stroke(width = width, cap = StrokeCap.Round)
            drawArc(trackColor, StartAngle, FullCircle, useCenter = false, topLeft = origin, size = arcSize, style = style)
            drawArc(
                indicatorColor, StartAngle, FullCircle * filled.value,
                useCenter = false, topLeft = origin, size = arcSize, style = style,
            )
        }
        BasicText(text = label, style = AppTheme.typography.label.copy(color = labelColor))
    }
}
