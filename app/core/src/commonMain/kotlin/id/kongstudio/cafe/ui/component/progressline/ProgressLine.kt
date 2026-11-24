package id.kongstudio.cafe.ui.component.progressline

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import id.kongstudio.cafe.resources.Res
import id.kongstudio.cafe.resources.common_loading
import id.kongstudio.cafe.ui.theme.AppTheme
import org.jetbrains.compose.resources.stringResource

private const val SegmentFraction = 0.4f

/** Garis progres tanpa persen untuk proses yang sedang berjalan; pemanggil menumpuknya di atas isi supaya tata letak tidak bergeser. */
@Composable
fun ProgressLine(modifier: Modifier = Modifier) {
    val colors = AppTheme.colors
    val effects = AppTheme.effects
    val description = stringResource(Res.string.common_loading)
    val progress by rememberInfiniteTransition(label = "progress-line").animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(effects.loopMillis, easing = effects.standard), RepeatMode.Restart),
        label = "progress-line-offset",
    )

    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(AppTheme.sizes.progressLine)
            .clipToBounds()
            .background(colors.selected)
            .semantics {
                contentDescription = description
                liveRegion = LiveRegionMode.Polite
            }
            .drawBehind {
                val segment = size.width * SegmentFraction
                val start = -segment + progress * (size.width + segment)
                drawRect(color = colors.primary, topLeft = Offset(start, 0f), size = Size(segment, size.height))
            },
    )
}
