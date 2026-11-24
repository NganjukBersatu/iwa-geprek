package id.kongstudio.cafe.ui.component.skeleton

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Shape
import id.kongstudio.cafe.ui.theme.AppTheme

private const val ShimmerDurationMs = 1_200

/** Blok penanda isi yang belum dimuat dengan kilau yang digambar di fase gambar, tanpa komposisi ulang tiap frame. */
@Composable
fun SkeletonBlock(
    modifier: Modifier = Modifier,
    shape: Shape = AppTheme.shapes.field,
) {
    val colors = AppTheme.colors
    val progress = rememberInfiniteTransition().animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(ShimmerDurationMs, easing = LinearEasing), RepeatMode.Restart),
    )

    Box(
        modifier = modifier
            .clip(shape)
            .drawBehind {
                val width = size.width
                val start = -width + progress.value * 2 * width
                drawRect(
                    brush = Brush.linearGradient(
                        colors = listOf(colors.selected, colors.surface, colors.selected),
                        start = Offset(start, 0f),
                        end = Offset(start + width, 0f),
                    ),
                )
            },
    )
}
