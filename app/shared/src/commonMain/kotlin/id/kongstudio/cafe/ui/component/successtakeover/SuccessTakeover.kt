package id.kongstudio.cafe.ui.component.successtakeover

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.Easing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import id.kongstudio.cafe.ui.component.appicon.AppIcon
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.pow
import kotlin.math.roundToInt
import kotlinx.coroutines.launch

private const val FloodMillis = 650
private const val BadgeMillis = 480
private const val CheckMillis = 420
private const val CheckDelayMillis = 220
private const val TextMillis = 420
private const val TextStaggerMillis = 90
private const val CountMillis = 900
private const val TextCount = 4
private const val TextMuteAlpha = 0.85f
private const val BadgeFillAlpha = 0.2f
private const val CheckStartScale = 0.4f
private val BadgeSize = 100.dp
private val CheckSize = 56.dp
private val TextRise = 14.dp
private val CountEasing = Easing { 1f - (1f - it).pow(3) }

/** Layar penuh yang dibanjiri [containerColor] dari tepi bawah lalu menggambar centang, menaikkan teks, dan menghitung [countTo] dari nol sampai ditutup lewat [onDone], dengan [eyebrow], [countCaption], [details], dan [badgeColor] opsional; bila [badgeColor] diisi, lingkaran centangnya berwarna itu penuh dengan centang [contentColor]. */
@Composable
fun SuccessTakeover(
    title: String,
    message: String,
    countTo: Int?,
    countLabel: @Composable (Int) -> String,
    actionLabel: String,
    containerColor: Color,
    contentColor: Color,
    onDone: () -> Unit,
    eyebrow: String? = null,
    countCaption: String? = null,
    badgeColor: Color? = null,
    details: (@Composable ColumnScope.() -> Unit)? = null,
) {
    val effects = AppTheme.effects
    val spacing = AppTheme.spacing
    val flood = remember { Animatable(0f) }
    val badge = remember { Animatable(0f) }
    val check = remember { Animatable(0f) }
    val texts = remember { List(TextCount) { Animatable(0f) } }
    val count = remember { Animatable(0f) }
    var closed by remember { mutableStateOf(false) }
    val close = {
        if (!closed) {
            closed = true
            onDone()
        }
    }

    LaunchedEffect(Unit) {
        flood.animateTo(1f, tween(FloodMillis, easing = effects.exit))
        launch { badge.animateTo(1f, tween(BadgeMillis, easing = effects.bounce)) }
        check.animateTo(1f, tween(CheckMillis, delayMillis = CheckDelayMillis, easing = effects.standard))
        texts.forEachIndexed { index, item ->
            launch { item.animateTo(1f, tween(TextMillis, delayMillis = index * TextStaggerMillis, easing = effects.emphasized)) }
        }
        count.animateTo(1f, tween(CountMillis, easing = CountEasing))
    }

    Dialog(
        onDismissRequest = close,
        properties = DialogProperties(dismissOnClickOutside = false, usePlatformDefaultWidth = false),
    ) {
        BoxWithConstraints(modifier = Modifier.fillMaxSize()) {
            val density = LocalDensity.current
            val width = constraints.maxWidth.toFloat()
            val height = constraints.maxHeight.toFloat()
            val lift = with(density) { (spacing.lg + spacing.touchTarget / 2).toPx() }
            val origin = Offset(width / 2f, height - WindowInsets.navigationBars.getBottom(density) - lift)
            val radius = hypot(max(origin.x, width - origin.x), max(origin.y, height - origin.y))

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .drawBehind { drawCircle(containerColor, radius = radius * flood.value, center = origin) }
                    .padding(horizontal = spacing.lg),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(spacing.sm, Alignment.CenterVertically),
            ) {
                eyebrow?.let {
                    BasicText(
                        text = it,
                        style = AppTheme.typography.label.copy(color = contentColor.copy(alpha = TextMuteAlpha), textAlign = TextAlign.Center),
                        modifier = Modifier.rise(texts[0]),
                    )
                }
                Badge(
                    scale = { badge.value },
                    progress = { check.value },
                    color = contentColor,
                    badgeColor = badgeColor,
                    modifier = Modifier.padding(bottom = spacing.sm),
                )
                BasicText(
                    text = title,
                    style = AppTheme.typography.title.copy(color = contentColor, textAlign = TextAlign.Center),
                    modifier = Modifier.rise(texts[0]),
                )
                if (countTo != null) {
                    countCaption?.let {
                        BasicText(
                            text = it,
                            style = AppTheme.typography.caption.copy(color = contentColor.copy(alpha = TextMuteAlpha), textAlign = TextAlign.Center),
                            modifier = Modifier.rise(texts[1]),
                        )
                    }
                    BasicText(
                        text = countLabel((countTo * count.value).roundToInt()),
                        style = AppTheme.typography.display.copy(color = contentColor, textAlign = TextAlign.Center),
                        modifier = Modifier.rise(texts[1]),
                    )
                }
                BasicText(
                    text = message,
                    style = AppTheme.typography.body.copy(
                        color = contentColor.copy(alpha = TextMuteAlpha),
                        textAlign = TextAlign.Center,
                    ),
                    modifier = Modifier.rise(texts[2]),
                )
                details?.let { content ->
                    Column(
                        modifier = Modifier
                            .rise(texts[2])
                            .widthIn(max = AppTheme.sizes.contentMaxWidth)
                            .fillMaxWidth(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(spacing.sm),
                        content = content,
                    )
                }
                BasicText(
                    text = actionLabel,
                    style = AppTheme.typography.button.copy(color = containerColor, textAlign = TextAlign.Center),
                    modifier = Modifier
                        .padding(top = spacing.xl)
                        .rise(texts[3])
                        .widthIn(max = AppTheme.sizes.contentMaxWidth)
                        .fillMaxWidth()
                        .clip(AppTheme.shapes.pill)
                        .background(contentColor)
                        .clickable(enabled = !closed, role = Role.Button, onClick = close)
                        .padding(horizontal = spacing.lg, vertical = spacing.md),
                )
            }
        }
    }
}

@Composable
private fun Badge(scale: () -> Float, progress: () -> Float, color: Color, badgeColor: Color?, modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .size(BadgeSize)
            .graphicsLayer {
                scaleX = scale()
                scaleY = scale()
            }
            .clip(CircleShape)
            .background(badgeColor ?: color.copy(alpha = BadgeFillAlpha)),
        contentAlignment = Alignment.Center,
    ) {
        AppIcon(
            icon = AppIcons.Check,
            tint = color,
            size = CheckSize,
            modifier = Modifier.graphicsLayer {
                alpha = progress()
                scaleX = CheckStartScale + (1f - CheckStartScale) * progress()
                scaleY = scaleX
            },
        )
    }
}

private fun Modifier.rise(progress: Animatable<Float, *>) = graphicsLayer {
    alpha = progress.value
    translationY = (1f - progress.value) * TextRise.toPx()
}
