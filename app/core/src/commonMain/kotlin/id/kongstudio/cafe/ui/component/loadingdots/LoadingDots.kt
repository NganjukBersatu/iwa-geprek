package id.kongstudio.cafe.ui.component.loadingdots

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.StartOffset
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_loading
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

private const val DotCount = 3
private const val DimAlpha = 0.35f

/** Tiga titik yang berdenyut bergantian, penanda proses yang sedang berjalan di dalam tombol. */
@Composable
fun LoadingDots(color: Color, modifier: Modifier = Modifier) {
    val effects = AppTheme.effects
    val description = stringResource(Res.string.common_loading)
    val transition = rememberInfiniteTransition(label = "loading-dots")

    Row(
        modifier = modifier.semantics { contentDescription = description },
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.xs),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        repeat(DotCount) { index ->
            val alpha by transition.animateFloat(
                initialValue = DimAlpha,
                targetValue = 1f,
                animationSpec = infiniteRepeatable(
                    animation = tween(effects.loopMillis / 2, easing = effects.standard),
                    repeatMode = RepeatMode.Reverse,
                    initialStartOffset = StartOffset(index * effects.loopMillis / (DotCount * 2)),
                ),
                label = "loading-dot-$index",
            )
            Box(
                modifier = Modifier
                    .size(AppTheme.spacing.sm)
                    .graphicsLayer { this.alpha = alpha }
                    .clip(AppTheme.shapes.pill)
                    .background(color),
            )
        }
    }
}
