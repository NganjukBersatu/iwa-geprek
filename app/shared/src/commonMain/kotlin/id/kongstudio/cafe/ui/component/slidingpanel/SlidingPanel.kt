package id.kongstudio.cafe.ui.component.slidingpanel

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.spring
import androidx.compose.foundation.gestures.Orientation
import androidx.compose.foundation.gestures.draggable
import androidx.compose.foundation.gestures.rememberDraggableState
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.layout
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.ui.component.panelhandle.PanelHandle
import kotlin.math.max
import kotlin.math.roundToInt
import kotlinx.coroutines.launch

enum class PanelSide { Start, End }

private const val Open = 1f
private const val Closed = 0f
private const val SettleThreshold = 0.5f
private const val DefaultExpandedFraction = 0.92f
private val FlingThreshold = 300.dp
private val NoInset = 0.dp
private val PanelSpring = spring<Float>(
    dampingRatio = Spring.DampingRatioNoBouncy,
    stiffness = Spring.StiffnessMediumLow,
)

/** Panel di tepi layar yang meluncur lewat satu gagang dan opsional melebar menutupi [content], dengan [panelWidth] sudah termasuk jarak luar dan [handleInset] menggeser gagang ke dalam. */
@Composable
fun SlidingPanel(
    side: PanelSide,
    hidden: Boolean,
    onHiddenChange: (Boolean) -> Unit,
    panelWidth: Dp,
    modifier: Modifier = Modifier,
    handleInset: Dp = NoInset,
    handleDescription: String = "",
    showHandle: Boolean = true,
    expanded: Boolean = false,
    expandedFraction: Float = DefaultExpandedFraction,
    badge: String? = null,
    panel: @Composable () -> Unit,
    content: @Composable () -> Unit,
) {
    val density = LocalDensity.current
    val scope = rememberCoroutineScope()
    val progress = remember { Animatable(if (hidden) Closed else Open) }
    val expand = remember { Animatable(if (expanded) Open else Closed) }
    val currentHidden by rememberUpdatedState(hidden)
    val currentOnHiddenChange by rememberUpdatedState(onHiddenChange)
    val atStart = side == PanelSide.Start
    val direction = if (atStart) 1f else -1f

    LaunchedEffect(hidden) { progress.animateTo(if (hidden) Closed else Open, PanelSpring) }
    LaunchedEffect(expanded) { expand.animateTo(if (expanded) Open else Closed, PanelSpring) }

    BoxWithConstraints(modifier = modifier.fillMaxSize()) {
        val baseWidthPx = with(density) { panelWidth.toPx() }
        val expandedWidthPx = with(density) { (maxWidth * expandedFraction).toPx() }
        val insetPx = with(density) { handleInset.toPx() }
        val flingPx = with(density) { FlingThreshold.toPx() }

        fun panelPx() = baseWidthPx + max(0f, expandedWidthPx - baseWidthPx) * expand.value

        val dragState = rememberDraggableState { delta ->
            scope.launch {
                progress.snapTo((progress.value + direction * delta / baseWidthPx).coerceIn(Closed, Open))
            }
        }

        val slot: @Composable () -> Unit = {
            Box(
                modifier = Modifier
                    .fillMaxHeight()
                    .layout { measurable, constraints ->
                        val width = panelPx().roundToInt()
                        val placeable = measurable.measure(Constraints.fixed(width, constraints.maxHeight))
                        val reserved = (baseWidthPx * progress.value).roundToInt()
                        // Panel lebar menutupi isi; saat menutup, panel keluar lewat tepinya sendiri.
                        val x = if (atStart) {
                            -panelPx() * (Open - progress.value)
                        } else {
                            (baseWidthPx - panelPx()) * progress.value
                        }
                        layout(reserved, constraints.maxHeight) { placeable.place(x.roundToInt(), 0) }
                    },
            ) { panel() }
        }

        Row(modifier = Modifier.fillMaxSize()) {
            if (atStart) slot()
            Box(modifier = Modifier.weight(1f).fillMaxHeight()) { content() }
            if (!atStart) slot()
        }

        if (showHandle) PanelHandle(
            atStart = atStart,
            hidden = hidden,
            description = handleDescription,
            badge = badge.takeIf { hidden },
            onClick = { currentOnHiddenChange(!currentHidden) },
            modifier = Modifier
                .align(if (atStart) Alignment.CenterStart else Alignment.CenterEnd)
                .offset {
                    val shift = ((panelPx() - insetPx) * progress.value).roundToInt()
                    IntOffset(if (atStart) shift else -shift, 0)
                }
                .draggable(
                    state = dragState,
                    orientation = Orientation.Horizontal,
                    onDragStopped = { velocity ->
                        val opening = direction * velocity
                        val open = when {
                            opening > flingPx -> true
                            opening < -flingPx -> false
                            else -> progress.value > SettleThreshold
                        }
                        if (open == !currentHidden) {
                            scope.launch {
                                progress.animateTo(
                                    if (open) Open else Closed,
                                    PanelSpring,
                                    initialVelocity = direction * velocity / baseWidthPx,
                                )
                            }
                        } else {
                            currentOnHiddenChange(!open)
                        }
                    },
                ),
        )
    }
}
