package id.kongstudio.cafe.ui.component.cryinglogo

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.StartOffset
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.State
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme

private val DefaultSize = 176.dp
private const val SwayMillis = 2600
private val DroopDistance = 5.dp
private const val TiltDegrees = 2f
private const val TearMillis = 1800
private const val TearOffsetMillis = 900

/** Satu tetes air mata pada logo, dalam pecahan lebar dan tinggi logo: kolom jatuhnya, dan awal serta akhir jatuhnya. */
private class Tear(val column: Float, val startY: Float, val endY: Float)

/** Letak mata pada logo merek 300 x 396, diukur dari pikselnya; logo itu bukan persegi, jadi letaknya dihitung terhadap gambar yang sudah dipaskan di dalam kotak. */
private const val LogoAspect = 300f / 396f
private val Tears = listOf(
    Tear(column = 150f / 300f, startY = 152f / 396f, endY = 176f / 396f),
    Tear(column = 210f / 300f, startY = 170f / 396f, endY = 194f / 396f),
)
private const val TearRadius = 3.5f / 300f
/** Jarak logo ke tepi kotaknya, dalam pecahan sisi kotak. */
private const val LogoPadding = 0.12f
private const val TearAlpha = 0.8f
private const val TearFadeInShare = 0.15f
private const val TearFadeOutShare = 0.3f
private const val BadgeScale = 0.28f
private const val BadgeIconScale = 0.17f

/** Logo merek di atas kotak warna utama, menangis, dengan lencana [badgeIcon] di pojok kanan bawah; letak air matanya dihitung untuk logo itu sehingga [painter] harus gambar itu. */
@Composable
fun CryingLogo(
    painter: Painter,
    badgeIcon: ImageVector,
    modifier: Modifier = Modifier,
    size: Dp = DefaultSize,
) {
    val colors = AppTheme.colors
    val transition = rememberInfiniteTransition(label = "crying-logo")
    val sway by transition.animateFloat(
        initialValue = -1f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(SwayMillis, easing = FastOutSlowInEasing), RepeatMode.Reverse),
        label = "sway",
    )
    val tears: List<State<Float>> = Tears.indices.map { index ->
        transition.animateFloat(
            initialValue = 0f,
            targetValue = 1f,
            animationSpec = infiniteRepeatable(
                animation = tween(TearMillis, easing = LinearEasing),
                repeatMode = RepeatMode.Restart,
                initialStartOffset = StartOffset(index * TearOffsetMillis),
            ),
            label = "tear-$index",
        )
    }

    Box(modifier = modifier.size(size)) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .clip(AppTheme.shapes.field)
                .background(colors.primary)
                .graphicsLayer {
                    translationY = (sway + 1f) / 2f * DroopDistance.toPx()
                    rotationZ = sway * TiltDegrees
                },
        ) {
            Image(painter = painter, contentDescription = null, contentScale = ContentScale.Fit, modifier = Modifier.fillMaxSize().padding(size * LogoPadding))
            Canvas(modifier = Modifier.fillMaxSize()) {
                val side = this.size.width
                val imageHeight = side * (1f - 2f * LogoPadding)
                val imageWidth = imageHeight * LogoAspect
                val left = (side - imageWidth) / 2f
                val top = side * LogoPadding
                Tears.forEachIndexed { index, tear ->
                    val phase = tears[index].value
                    val fade = minOf(phase / TearFadeInShare, (1f - phase) / TearFadeOutShare, 1f)
                    val y = top + imageHeight * (tear.startY + (tear.endY - tear.startY) * phase)
                    drawPath(
                        path = teardrop(centerX = left + imageWidth * tear.column, centerY = y, radius = imageWidth * TearRadius),
                        color = colors.info.copy(alpha = TearAlpha * fade),
                    )
                }
            }
        }
        Box(
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .size(size * BadgeScale)
                .clip(AppTheme.shapes.pill)
                .background(colors.accentSurface),
            contentAlignment = Alignment.Center,
        ) {
            AppIcon(icon = badgeIcon, tint = colors.content, size = size * BadgeIconScale)
        }
    }
}

private fun teardrop(centerX: Float, centerY: Float, radius: Float): Path {
    val top = centerY - radius * 2f
    return Path().apply {
        moveTo(centerX, top)
        cubicTo(centerX + radius * 0.3f, top + radius * 0.8f, centerX + radius, centerY - radius * 0.8f, centerX + radius, centerY)
        cubicTo(centerX + radius, centerY + radius * 0.55f, centerX + radius * 0.55f, centerY + radius, centerX, centerY + radius)
        cubicTo(centerX - radius * 0.55f, centerY + radius, centerX - radius, centerY + radius * 0.55f, centerX - radius, centerY)
        cubicTo(centerX - radius, centerY - radius * 0.8f, centerX - radius * 0.3f, top + radius * 0.8f, centerX, top)
        close()
    }
}
