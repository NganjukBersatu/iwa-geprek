package id.kongstudio.cafe.ui.component.kanbanboard

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.layout.positionInRoot
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import id.kongstudio.cafe.ui.theme.AppTheme
import kotlin.math.roundToInt

private val ColumnMinWidth = 240.dp

/** Satu kolom papan; [accent] menjadi penanda judul dan sorot saat kolom jadi tujuan seret. */
@Immutable
class KanbanColumn<T>(
    val key: String,
    val title: String,
    val accent: Color,
    val items: List<T>,
)

/** Papan kolom berisi kartu yang dipindah antarkolom dengan menekan lama lalu menyeret, dengan kartu digambar pemanggil lewat [card]. */
@Composable
fun <T : Any> KanbanBoard(
    columns: List<KanbanColumn<T>>,
    itemKey: (T) -> String,
    emptyText: @Composable (KanbanColumn<T>) -> String,
    onMove: (item: T, toColumnKey: String) -> Unit,
    modifier: Modifier = Modifier,
    canDrag: (T) -> Boolean = { true },
    onItemClick: (T) -> Unit = {},
    onDragActiveChange: (Boolean) -> Unit = {},
    card: @Composable (T) -> Unit,
) {
    val spacing = AppTheme.spacing
    val density = LocalDensity.current
    val drag = remember { KanbanDragState<T>() }
    val bounds = remember { mutableStateMapOf<String, Rect>() }
    var origin by remember { mutableStateOf(Offset.Zero) }
    val currentOnMove by rememberUpdatedState(onMove)
    val currentActiveChange by rememberUpdatedState(onDragActiveChange)

    fun columnAtPointer(): String? = bounds.entries.firstOrNull { it.value.contains(drag.pointer) }?.key

    val callbacks = remember(drag) {
        KanbanDragCallbacks<T>(
            onStart = { item, columnKey, cardTopLeft, cardSize, grab ->
                drag.start(item, columnKey, cardTopLeft, cardSize, grab)
                currentActiveChange(true)
            },
            onMove = drag::move,
            onEnd = {
                val item = drag.item
                val target = columnAtPointer()
                val source = drag.fromColumn
                drag.clear()
                currentActiveChange(false)
                if (item != null && target != null && target != source) currentOnMove(item, target)
            },
            onCancel = {
                drag.clear()
                currentActiveChange(false)
            },
        )
    }

    val hovered = if (drag.active) columnAtPointer() else null
    val draggingKey = drag.item?.let(itemKey)

    BoxWithConstraints(
        modifier = modifier
            .fillMaxSize()
            .onGloballyPositioned { origin = it.positionInRoot() },
    ) {
        val fits = maxWidth >= ColumnMinWidth * columns.size
        Row(
            modifier = Modifier
                .fillMaxSize()
                .then(if (fits) Modifier else Modifier.horizontalScroll(rememberScrollState())),
            horizontalArrangement = Arrangement.spacedBy(spacing.sm),
        ) {
            columns.forEach { column ->
                KanbanColumnView(
                    column = column,
                    itemKey = itemKey,
                    emptyText = emptyText(column),
                    highlighted = hovered == column.key,
                    draggingKey = draggingKey,
                    canDrag = canDrag,
                    drag = callbacks,
                    onItemClick = onItemClick,
                    onBounds = { bounds[column.key] = it },
                    modifier = (if (fits) Modifier.weight(1f) else Modifier.width(ColumnMinWidth)).fillMaxHeight(),
                    card = card,
                )
            }
        }

        drag.item?.let { item ->
            val local = drag.ghostTopLeft - origin
            Box(
                modifier = Modifier
                    .offset { IntOffset(local.x.roundToInt(), local.y.roundToInt()) }
                    .width(with(density) { drag.size.width.toDp() }),
            ) {
                card(item)
            }
        }
    }
}
