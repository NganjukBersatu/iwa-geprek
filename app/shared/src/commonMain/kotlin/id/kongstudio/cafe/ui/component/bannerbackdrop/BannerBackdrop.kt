package id.kongstudio.cafe.ui.component.bannerbackdrop

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.ui.theme.AppTheme

private val WaveHeight = 36.dp
private val RingRadii = listOf(64.dp, 104.dp, 144.dp, 184.dp)
private val RingAlphas = listOf(0.30f, 0.22f, 0.15f, 0.09f)
private val RingStroke = 2.dp
private val RingInsetEnd = 18.dp
private val RingInsetTop = 14.dp
private val BubbleRadii = listOf(96.dp, 56.dp)
private val BubbleInsetStart = 18.dp
private val BubbleInsetBottom = 64.dp
private const val BubbleAlpha = 0.06f
private val LargeDotRadius = 5.dp
private val LargeDotInsetEnd = 72.dp
private val LargeDotInsetTop = 120.dp
private const val LargeDotAlpha = 0.55f
private val SmallDotRadius = 3.dp
private val SmallDotInsetEnd = 48.dp
private val SmallDotInsetTop = 150.dp
private const val SmallDotAlpha = 0.4f

/** Gelombang simetris dua lengkung, dirancang pada kotak 390 x 36 lalu diskalakan mengikuti lebar dan tinggi sebenarnya. */
private const val WaveDesignWidth = 390f
private const val WaveDesignHeight = 36f

/** Pita warna primary di puncak layar: lingkaran dekoratif dan tepi bawah bergelombang; [content] berada di atasnya. */
@Composable
fun BannerBackdrop(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit,
) {
    val colors = AppTheme.colors

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clipToBounds()
            .drawBehind {
                drawBanner(
                    base = colors.primary,
                    accent = colors.accent,
                    bubble = colors.onPrimary,
                    wave = colors.background,
                )
            }
            .padding(bottom = WaveHeight),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
        content = content,
    )
}

private fun DrawScope.drawBanner(base: Color, accent: Color, bubble: Color, wave: Color) {
    drawRect(base)

    val ringCenter = Offset(size.width - RingInsetEnd.toPx(), RingInsetTop.toPx())
    RingRadii.forEachIndexed { index, radius ->
        drawCircle(
            color = accent.copy(alpha = RingAlphas[index]),
            radius = radius.toPx(),
            center = ringCenter,
            style = Stroke(width = RingStroke.toPx()),
        )
    }

    val bubbleCenter = Offset(BubbleInsetStart.toPx(), size.height - BubbleInsetBottom.toPx())
    BubbleRadii.forEach { radius ->
        drawCircle(color = bubble.copy(alpha = BubbleAlpha), radius = radius.toPx(), center = bubbleCenter)
    }

    drawCircle(
        color = accent.copy(alpha = LargeDotAlpha),
        radius = LargeDotRadius.toPx(),
        center = Offset(size.width - LargeDotInsetEnd.toPx(), LargeDotInsetTop.toPx()),
    )
    drawCircle(
        color = accent.copy(alpha = SmallDotAlpha),
        radius = SmallDotRadius.toPx(),
        center = Offset(size.width - SmallDotInsetEnd.toPx(), SmallDotInsetTop.toPx()),
    )

    drawPath(wavePath(), wave)
}

private fun DrawScope.wavePath(): Path {
    val scaleX = size.width / WaveDesignWidth
    val height = WaveHeight.toPx()
    val scaleY = height / WaveDesignHeight
    val top = size.height - height

    return Path().apply {
        moveTo(0f, size.height)
        lineTo(0f, top + 16f * scaleY)
        cubicTo(65f * scaleX, top + 36f * scaleY, 130f * scaleX, top + 36f * scaleY, 195f * scaleX, top + 16f * scaleY)
        cubicTo(260f * scaleX, top + 36f * scaleY, 325f * scaleX, top + 36f * scaleY, size.width, top + 16f * scaleY)
        lineTo(size.width, size.height)
        close()
    }
}
