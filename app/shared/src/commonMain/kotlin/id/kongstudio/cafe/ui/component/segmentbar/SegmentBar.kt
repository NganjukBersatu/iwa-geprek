package id.kongstudio.cafe.ui.component.segmentbar

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import id.kongstudio.cafe.ui.theme.AppTheme

/** Bagian terkecil yang tetap bisa disentuh, sebagai porsi lebar seluruh bilah. */
private const val MinShare = 0.14f

enum class BarTone { Primary, Accent }

/** Satu bagian bilah: [weight] menentukan lebar relatif dan [progress] 0..1 mengisi dari kiri. */
@Immutable
class BarSegment(
    val weight: Float,
    val progress: Float,
    val tone: BarTone,
)

/** Bilah berbagian yang lebarnya sebanding bobot, tanpa bingkai; setiap bagian bisa diketuk. */
@Composable
fun SegmentBar(
    segments: List<BarSegment>,
    onSelect: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = AppTheme.colors
    val effects = AppTheme.effects
    val shape = AppTheme.shapes.field
    val total = segments.sumOf { it.weight.toDouble() }.toFloat().coerceAtLeast(1f)

    Row(
        modifier = modifier.fillMaxWidth().height(AppTheme.spacing.xxxl),
        horizontalArrangement = Arrangement.spacedBy(AppTheme.spacing.sm),
    ) {
        segments.forEachIndexed { index, segment ->
            val fill by animateFloatAsState(
                targetValue = segment.progress.coerceIn(0f, 1f),
                animationSpec = tween(effects.standardMillis, easing = effects.standard),
                label = "segment-fill",
            )
            Box(
                modifier = Modifier
                    .weight(segment.weight.coerceAtLeast(total * MinShare))
                    .fillMaxHeight()
                    .clip(shape)
                    .background(colors.selected)
                    .clickable(role = Role.Button) { onSelect(index) },
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxHeight()
                        .fillMaxWidth(fill)
                        .background(if (segment.tone == BarTone.Primary) colors.primary else colors.accent),
                )
            }
        }
    }
}
