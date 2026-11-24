package id.kongstudio.cafe.ui.component.scaletoheight

import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.Dp

private const val MinScale = 0.7f
private const val MaxScale = 1.5f

/** Memperbesar atau memperkecil isi (teks, ikon, jarak) mengikuti tinggi yang diberikan; [baseline] adalah tinggi alaminya, [baselineWidth] lebar alami yang membatasi skala agar isi tidak terpotong. */
/** Skala yang dipakai [ScaleToHeight] untuk tinggi [available] terhadap [baseline]; dipakai blok yang tingginya mengikuti isi tetapi skalanya mengikuti layar. */
fun scaleForHeight(available: Dp, baseline: Dp): Float = (available / baseline).coerceIn(MinScale, MaxScale)

/** Menerapkan [scale] pada isi tanpa membatasi tingginya, sehingga tinggi blok mengikuti isinya. */
@Composable
fun ScaledDensity(scale: Float, content: @Composable () -> Unit) {
    val density = LocalDensity.current
    CompositionLocalProvider(
        LocalDensity provides Density(density.density * scale, density.fontScale),
    ) { content() }
}

@Composable
fun ScaleToHeight(
    baseline: Dp,
    baselineWidth: Dp = Dp.Unspecified,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    BoxWithConstraints(modifier = modifier) {
        val density = LocalDensity.current
        val byHeight = maxHeight / baseline
        val byWidth = if (baselineWidth == Dp.Unspecified) Float.MAX_VALUE else maxWidth / baselineWidth
        val scale = minOf(byHeight, byWidth).coerceIn(MinScale, MaxScale)

        CompositionLocalProvider(
            LocalDensity provides Density(density.density * scale, density.fontScale),
        ) { content() }
    }
}
