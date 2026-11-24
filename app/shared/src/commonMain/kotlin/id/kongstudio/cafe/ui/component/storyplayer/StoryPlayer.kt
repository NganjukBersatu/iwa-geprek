package id.kongstudio.cafe.ui.component.storyplayer

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.BasicText
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.ui.component.iconbutton.AppIconButton
import id.kongstudio.cafe.ui.component.storytransition.StoryTransitionKind
import id.kongstudio.cafe.ui.component.storytransition.storyTransition
import id.kongstudio.cafe.ui.component.markdown.MarkdownContent
import id.kongstudio.cafe.ui.theme.AppTheme
import id.kongstudio.cafe.ui.theme.icon.AppIcons

private val SwipeThreshold = 56.dp

class StoryPage(val title: String, val body: String)

/** Pemutar halaman cerita dengan batang kemajuan, geser atau tombol untuk berpindah, peralihan berganti, dan halaman panjang bisa digulir. */
@Composable
fun StoryPlayer(
    pages: List<StoryPage>,
    previousLabel: String,
    nextLabel: String,
    finishLabel: String,
    progressLabel: (current: Int, total: Int) -> String,
    onFinish: () -> Unit,
    modifier: Modifier = Modifier,
    title: String? = null,
) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing
    val effects = AppTheme.effects
    val kinds = StoryTransitionKind.entries
    var index by rememberSaveable { mutableIntStateOf(0) }
    var forward by remember { mutableStateOf(true) }
    val last = pages.lastIndex
    val threshold = with(LocalDensity.current) { SwipeThreshold.toPx() }

    fun previous() {
        if (index > 0) {
            forward = false
            index -= 1
        }
    }

    fun next() {
        if (index < last) {
            forward = true
            index += 1
        } else {
            onFinish()
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = AppTheme.windowSize.pagePadding, vertical = spacing.lg),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(spacing.md),
    ) {
        Column(
            modifier = Modifier.widthIn(max = AppTheme.sizes.contentMaxWidth).weight(1f).fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(spacing.md),
        ) {
            Segments(count = pages.size, current = index)
            if (title != null) {
                BasicText(text = title, style = AppTheme.typography.label.copy(color = colors.contentMuted))
            }
            AnimatedContent(
                targetState = index,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .pointerInput(index) {
                        var travelled = 0f
                        detectHorizontalDragGestures(
                            onDragStart = { travelled = 0f },
                            onDragCancel = { travelled = 0f },
                            onDragEnd = {
                                when {
                                    travelled <= -threshold -> next()
                                    travelled >= threshold -> previous()
                                }
                            },
                        ) { _, delta -> travelled += delta }
                    },
                transitionSpec = {
                    storyTransition(
                        kind = kinds[targetState % kinds.size],
                        forward = forward,
                        millis = effects.slowMillis,
                        easing = effects.emphasized,
                    )
                },
                label = "story-page",
            ) { page ->
                Page(pages[page])
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                AppIconButton(
                    icon = AppIcons.ChevronLeft,
                    contentDescription = previousLabel,
                    onClick = ::previous,
                    tint = if (index > 0) colors.content else colors.contentMuted.copy(alpha = colors.disabledAlpha),
                )
                BasicText(
                    text = progressLabel(index + 1, pages.size),
                    style = AppTheme.typography.label.copy(color = colors.contentMuted),
                )
                AppIconButton(
                    icon = if (index == last) AppIcons.Close else AppIcons.ChevronRight,
                    contentDescription = if (index == last) finishLabel else nextLabel,
                    onClick = ::next,
                )
            }
        }
    }
}

@Composable
private fun Segments(count: Int, current: Int) {
    val spacing = AppTheme.spacing
    val colors = AppTheme.colors
    val effects = AppTheme.effects

    // Tinggi baris tetap setebal segmen terbaca supaya tata letak tidak melompat saat segmen berganti.
    Row(
        modifier = Modifier.fillMaxWidth().height(spacing.sm),
        horizontalArrangement = Arrangement.spacedBy(spacing.xs),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        repeat(count) { i ->
            val read = i <= current
            // Outline lolos kontras 3:1 terhadap latar tetapi mirip primary, jadi ketebalan ikut membedakan.
            val color by animateColorAsState(
                targetValue = if (read) colors.primary else colors.outline,
                animationSpec = tween(effects.standardMillis),
                label = "story-segment",
            )
            Box(
                modifier = Modifier
                    .weight(1f)
                    .height(if (read) spacing.sm else spacing.xs)
                    .clip(AppTheme.shapes.pill)
                    .background(color),
            )
        }
    }
}

@Composable
private fun Page(page: StoryPage) {
    val colors = AppTheme.colors
    val spacing = AppTheme.spacing

    Column(
        modifier = Modifier
            .fillMaxSize()
            .clip(AppTheme.shapes.card)
            .background(colors.surface)
            .verticalScroll(rememberScrollState())
            .padding(spacing.lg),
        verticalArrangement = Arrangement.spacedBy(spacing.md),
    ) {
        BasicText(text = page.title, style = AppTheme.typography.headline.copy(color = colors.content))
        MarkdownContent(source = page.body)
    }
}
